package main

// To build for Wayland, use `go run -tags wayland net_gui.go` or
// `go build -tags wayland net_gui.go`.

import (
	"fmt"
	"net"
	"os/exec"
	"strings"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/theme"
	"fyne.io/fyne/v2/widget"
	"github.com/j-keck/arping"
)

type Device struct {
	IP       string
	Hostname string
	MAC      string
	New      bool
}

func incIP(ip net.IP) {
	for j := len(ip) - 1; j >= 0; j-- {
		ip[j]++
		if ip[j] > 0 {
			break
		}
	}
}

func scanNetwork(subnet string, known map[string]bool) ([]Device, error) {
	_, ipnet, err := net.ParseCIDR(subnet)
	if err != nil {
		return nil, err
	}
	var devices []Device
	arping.SetTimeout(500 * time.Millisecond)
	for ip := ipnet.IP.Mask(ipnet.Mask); ipnet.Contains(ip); incIP(ip) {
		if ip.Equal(ipnet.IP) {
			continue // skip network address
		}
		hw, _, err := arping.Ping(ip)
		if err != nil {
			continue
		}
		var hostname string
		if names, err := net.LookupAddr(ip.String()); err == nil && len(names) > 0 {
			hostname = strings.TrimSuffix(names[0], ".")
		}
		macStr := hw.String()
		newHost := !known[macStr]
		known[macStr] = true
		devices = append(devices, Device{
			IP:       ip.String(),
			Hostname: hostname,
			MAC:      macStr,
			New:      newHost,
		})
	}
	return devices, nil
}

// GUI application
func main() {
	a := app.New()
	w := a.NewWindow("Network Scanner")

	subnet := widget.NewEntry()
	subnet.SetText("192.168.1.0/24")

	var devices []Device
	known := make(map[string]bool)
	list := widget.NewList(
		func() int { return len(devices) },
		func() fyne.CanvasObject {
			rect := canvas.NewRectangle(theme.PrimaryColor())
			rect.SetMinSize(fyne.NewSize(16, 16))
			ip := widget.NewLabel("")
			host := widget.NewLabel("")
			mac := widget.NewLabel("")
			return container.NewHBox(rect, ip, host, mac)
		},
		func(id widget.ListItemID, o fyne.CanvasObject) {
			dev := devices[id]
			c := o.(*fyne.Container)
			rect := c.Objects[0].(*canvas.Rectangle)
			if dev.New {
				rect.FillColor = theme.PrimaryColor()
			} else {
				rect.FillColor = theme.ForegroundColor()
			}
			c.Objects[1].(*widget.Label).SetText(dev.IP)
			c.Objects[2].(*widget.Label).SetText(dev.Hostname)
			c.Objects[3].(*widget.Label).SetText(dev.MAC)
			rect.Refresh()
		},
	)

	list.OnSelected = func(id widget.ListItemID) {
		dev := devices[id]
		startWebSSH(dev.IP)
	}

	status := canvas.NewText("", theme.ForegroundColor())

	scanBtn := widget.NewButton("Scan", func() {
		status.Text = "Scanning..."
		status.Refresh()
		go func() {
			devs, err := scanNetwork(subnet.Text, known)
			if err != nil {
				fyne.Do(func() {
					status.Text = fmt.Sprintf("Error: %v", err)
					status.Refresh()
				})
				return
			}
			devices = devs
			fyne.Do(func() {
				status.Text = fmt.Sprintf("Found %d devices", len(devices))
				status.Refresh()
				list.Refresh()
			})
		}()
	})

	w.SetContent(container.NewBorder(
		container.NewVBox(subnet, scanBtn, status), nil, nil, nil, list,
	))
	w.Resize(fyne.NewSize(600, 400))
	w.ShowAndRun()
}

func startWebSSH(ip string) {
	// start webssh if not running
	cmd := exec.Command("wssh", "--address", "127.0.0.1", "--port", "8888", "--policy", "autoadd", "--redirect", "False")
	if err := cmd.Start(); err == nil {
		go cmd.Wait()
		// allow server to start
		time.Sleep(500 * time.Millisecond)
	}
	exec.Command("xdg-open", fmt.Sprintf("http://localhost:8888/?hostname=%s&port=22", ip)).Start()
}
