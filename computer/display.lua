local exports = {}

exports.MONITOR_ROWS = 6
exports.MONITOR_COLS = 11

local f = fs.open("monitors.json", "r")
---@cast f ReadHandle
local ids = textutils.unserialiseJSON(f.readAll())
f.close()

function exports.calibrate()
    local ids = {}
    print("Calibrating monitors")

    local total = exports.MONITOR_ROWS * exports.MONITOR_COLS
    for i = 1, total, 1 do
        local _, id = os.pullEvent("monitor_touch")
        local monitor = peripheral.wrap(id)
        monitor.clear()
        monitor.write(tostring(id) .. ": " .. tostring(i) .. "/" .. tostring(total))
        ids[#ids + 1] = id
    end

    local f = fs.open("monitors.json", "w")
    f.write(textutils.serialiseJSON(ids))
    f.close()
end

function exports.getMonitors()
    local monitor_count = exports.MONITOR_COLS * exports.MONITOR_ROWS
    local monitors = {}

    for i = 1, monitor_count, 1 do
        local id = ids[i]
        local monitor = peripheral.wrap(id)
        monitors[#monitors + 1] = monitor
    end

    return monitors
end

function exports.getDisplayString()
    local cols = exports.MONITOR_COLS
    local rows = exports.MONITOR_ROWS
    local width, height = exports.getIndivualMonitorSize()
    return string.format("%d-%d-%d-%d", rows, cols, width, height)
end

function exports.getIndivualMonitorSize()
    local monitor = peripheral.wrap(ids[1])
    local width, height = monitor.getSize()
    return width, height
end

local function resetMonitors()
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

resetMonitors()
return exports
