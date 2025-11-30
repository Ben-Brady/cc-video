local utils = require("utils")
local display = require("display")

local exports = {}

local monitor = peripheral.wrap("left")
local width, height = monitor.getSize()

local window_banner = window.create(monitor, 1, 1, width, 1, true)
local window_info = window.create(monitor, 2, height - 8 - 1, width, 8, true)

local function writeInfo(y, text)
    window_info.setVisible(false)
    window_info.setCursorPos(1, y)
    window_info.clearLine()
    window_info.write(text)
    window_info.setVisible(true)
end

function exports.initialise()
    window_info.clear()
    window_info.setCursorPos(1, 1)
    writeInfo(5, "      Stream: Starting")

    window_banner.setBackgroundColor(colors.gray)
    window_banner.setTextColor(colors.lightBlue)

    local BANNER = "YOUTUBE PLAYER"
    window_banner.write(string.rep(" ", width))

    window_banner.setCursorPos((width - #BANNER) / 2, 1)
    window_banner.write(BANNER)

    local mw, mh = display.getIndivualMonitorSize()
    local res_w = tostring(display.MONITOR_ROWS * mw)
    local res_h = tostring(display.MONITOR_COLS * mh)
    writeInfo(11, "   Resolution: " .. res_w .. "x" .. res_h)
    writeInfo(12, "         Rows: " .. tostring(display.MONITOR_ROWS) .. " x " .. tostring(mw) .. "px")
    writeInfo(13, "         Cols: " .. tostring(display.MONITOR_COLS) .. " x " .. tostring(mh) .. "px")
end

---@param value "loading" | "fine" | "ended"
function exports.setStream(value)
    if value == "loading" then
        writeInfo(5, "      Stream: Loading...")
    elseif value == "ended" then
        writeInfo(5, "      Stream: Finished")
    else
        writeInfo(5, "      Stream: Fine")
    end
end

---@param value boolean
function exports.setBufferLoading(value)
    if value then
        writeInfo(6, "      Buffer: Loading...")
    else
        writeInfo(6, "      Buffer: Fine")
    end
end

---@param value {
---    time: number,
---    renderDuration: number,
---    frameDuration: number,
---    videoBuffer: number,
---    audioBuffer: number,
function exports.setFrameInfo(value)
    writeInfo(1, "        Time: " .. utils.round(value.time, 2) .. "s")
    writeInfo(2, "  Render Dur: " .. utils.round(value.renderDuration * 1000, 2) .. "ms")
    writeInfo(3, "Playback Dur: " .. utils.round(value.frameDuration * 1000, 2) .. "ms")

    writeInfo(7, "Audio Buffer: " .. tostring(value.audioBuffer))
    writeInfo(8, "Video Buffer: " .. tostring(value.videoBuffer))
end

return exports
