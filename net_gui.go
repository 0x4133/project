package main

import (
    "context"
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
}

func incIP(ip net.IP) {
    for j := len(ip) - 1; j >= 0; j-- {
        ip[j]++
        if ip[j] > 0 {
            break
        }
    }
}

func scanNetwork(subnet string) ([]Device, error) {
    _, ipnet, err := net.ParseCIDR(subnet)
    if err != nil {
        return nil, err
    }
    var devices []Device
    for ip := ipnet.IP.Mask(ipnet.Mask); ipnet.Contains(ip); incIP(ip) {
        if ip.Equal(ipnet.IP) {
            continue // skip network address
        }
        ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
        hw, _, err := arping.PingContext(ctx, ip)
        cancel()
        if err != nil {
            continue
        }
        var hostname string
        if names, err := net.LookupAddr(ip.String()); err == nil && len(names) > 0 {
            hostname = strings.TrimSuffix(names[0], ".")
        }
        devices = append(devices, Device{
            IP:       ip.String(),
            Hostname: hostname,
            MAC:      hw.String(),
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
    table := widget.NewTable(
        func() (int, int) { return len(devices) + 1, 3 },
        func() fyne.CanvasObject {
            return container.NewHBox(
                widget.NewLabel(""),
                widget.NewLabel(""),
                widget.NewLabel(""),
            )
        },
        func(id widget.TableCellID, o fyne.CanvasObject) {
            labels := o.(*fyne.Container).Objects
            if id.Row == 0 {
                titles := []string{"IP", "Hostname", "MAC"}
                labels[0].(*widget.Label).SetText(titles[id.Col])
                labels[0].(*widget.Label).TextStyle = fyne.TextStyle{Bold: true}
                labels[1].(*widget.Label).SetText("")
                labels[2].(*widget.Label).SetText("")
                o.(*fyne.Container).Objects = labels
                return
            }
            dev := devices[id.Row-1]
            values := []string{dev.IP, dev.Hostname, dev.MAC}
            labels[0].(*widget.Label).SetText(values[id.Col])
        },
    )

    table.OnSelected = func(id widget.TableCellID) {
        if id.Row == 0 {
            return
        }
        dev := devices[id.Row-1]
        startWebSSH(dev.IP)
    }

    status := canvas.NewText("", theme.ForegroundColor())

    scanBtn := widget.NewButton("Scan", func() {
        status.Text = "Scanning..."
        status.Refresh()
        go func() {
            devs, err := scanNetwork(subnet.Text)
            if err != nil {
                status.Text = fmt.Sprintf("Error: %v", err)
                status.Refresh()
                return
            }
            devices = devs
            a.Queue().Add(func() {
                status.Text = fmt.Sprintf("Found %d devices", len(devices))
                status.Refresh()
                table.Refresh()
            })
        }()
    })

    w.SetContent(container.NewBorder(
        container.NewVBox(subnet, scanBtn, status), nil, nil, nil, table,
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

