local display = {}

---@class MonitorConfig
---@field ids string[]
---@field rows number
---@field cols number

---@type MonitorConfig?
local _config

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

---@return MonitorConfig|nil
local function readConfig()
    local f = fs.open("monitors.json", "r")
    if f == nil then
        return nil
    end

    local text = f.readAll()
    f.close()
    ---@cast text string

    local config = textutils.unserialiseJSON(text)
    ---@cast config MonitorConfig
    assert(config["rows"] ~= nil, "'rows' not in config")
    assert(config["cols"] ~= nil, "'cols' not in config")
    assert(config["ids"] ~= nil, "'ids' not in config")

    return config
end

---@param config MonitorConfig
local function writeConfig(config)
    local f = fs.open("monitors.json", "w")
    ---@cast f WriteHandle
    f.write(textutils.serialiseJSON(config))
    f.close()
end

function display.initialise()
    resetMonitors()
    _config = readConfig()

    if _config == nil then
        display.calibrate()
        _config = readConfig()
    end
end

---@return MonitorConfig
function display.getConfig()
    if _config == nil then
        error("Monitors not initialised")
    end

    return _config
end

function display.calibrate()
    local cols
    print("Calibrating")
    while cols == nil do
        write("  Columns: ")
        cols = tonumber(read())
    end

    local rows
    while rows == nil do
        write("  Rows: ")
        rows = tonumber(read())
    end


    print("  Click each monitor from top left to bottom right")
    local ids = {}
    local total = cols * rows
    for i = 1, total, 1 do
        local _, id = os.pullEvent("monitor_touch")
        local monitor = peripheral.wrap(id)
        ---@cast monitor Monitor

        monitor.clear()
        monitor.write(tostring(id) .. ": " .. tostring(i) .. "/" .. tostring(total))
        ids[#ids + 1] = id
    end

    resetMonitors()

    writeConfig({
        ids = ids,
        rows = rows,
        cols = cols
    })
    print("Calibration Complete")
end

function display.getMonitors()
    local config = display.getConfig()
    local monitor_count = config.rows * config.cols
    local monitors = {}

    for i = 1, monitor_count, 1 do
        local id = config.ids[i]
        local monitor = peripheral.wrap(id)
        monitors[#monitors + 1] = monitor
    end

    return monitors
end

function display.getDisplayString()
    local config = display.getConfig()
    local width, height = display.getIndivualMonitorSize()
    return string.format("%d-%d-%d-%d", config.rows, config.cols, width, height)
end

function display.getIndivualMonitorSize()
    local config = display.getConfig()
    local monitor = peripheral.wrap(config.ids[1])

    local width, height = monitor.getSize()
    return width, height
end

return display
