local exports = {}

exports.MONITOR_ROWS = 6
exports.MONITOR_COLS = 11
function exports.calibrate()
    local ids = {}
    for i = 1, exports.MONITOR_ROWS * exports.MONITOR_COLS, 1 do
        local _, id = os.pullEvent("monitor_touch")
        local monitor = peripheral.wrap(id)
        monitor.clear()
        monitor.write(id)
        ids[#ids + 1] = id
    end

    local f = fs.open("monitors.json", "w")
    f.write(textutils.serialiseJSON(ids))
    f.close()
end


function exports.setupMonitors()
    local f = fs.open("monitors.json", "r")
    local ids = textutils.unserialiseJSON(f.readAll())
    f.close()

    local monitors = {}
    for i, id in ipairs(ids) do
        local monitor = peripheral.wrap(id)
        monitors[#monitors + 1] = monitor
    end

    return monitors
end

function exports.resetMonitors()
    local colorIndexs = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 }

    ---@type Monitor[]
    local monitors = { peripheral.find("monitor") }
    for _, monitor in ipairs(monitors) do
        monitor.clear()
        monitor.setCursorPos(1, 1)
        monitor.setTextScale(0.5)

        for i, index in ipairs(colorIndexs) do
            local r, g, b = term.nativePaletteColour(index)
            monitor.setPaletteColor(index, colors.packRGB(r, g, b))
        end

        monitor.setPaletteColor(colors.black, 0)
    end

    return monitors
end

return exports
