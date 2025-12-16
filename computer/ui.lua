local utils = require("utils")
local display = require("display")

local exports = {}

local monitor = peripheral.wrap("right")
if monitor == nil then
    error("Monitor not on right side")
end
---@cast monitor Monitor

local width, height = monitor.getSize()

local window_banner = window.create(monitor, 1, 1, width, 1, true)
local window_info = window.create(monitor, 2, height - 9 - 1, width, 9, true)

local function writeInfo(y, text)
    window_info.setVisible(false)
    window_info.setCursorPos(1, y)
    window_info.clearLine()
    window_info.write(text)
    window_info.setVisible(true)
end

local function initialRender()
    local mw, mh = display.getIndivualMonitorSize()
    local res_w = tostring(display.MONITOR_ROWS * mw)
    local res_h = tostring(display.MONITOR_COLS * mh)
    writeInfo(11, "   Resolution: " .. res_w .. "x" .. res_h)
    writeInfo(12, "         Rows: " .. tostring(display.MONITOR_ROWS) .. " x " .. tostring(mw) .. "px")
    writeInfo(13, "         Cols: " .. tostring(display.MONITOR_COLS) .. " x " .. tostring(mh) .. "px")
end

function exports.initialise()
    window_info.clear()
    window_info.setCursorPos(1, 1)

    window_banner.setBackgroundColor(colors.gray)
    window_banner.setTextColor(colors.lightBlue)

    local BANNER = "YOUTUBE PLAYER"
    window_banner.write(string.rep(" ", width))

    window_banner.setCursorPos((width - #BANNER) / 2, 1)
    window_banner.write(BANNER)

    initialRender()
end

---@alias StreamInfoState "none" | "loading" | "fine"

---@type StreamInfoState
local streamState = "none"

---@param value StreamInfoState
function exports.setStream(value)
    streamState = value
end

---@type PlayerDebugInfo | nil
local playerInfo = nil

---@param value PlayerDebugInfo|nil
function exports.updatePlayerDebug(value)
    playerInfo = value
end

local function render()
    local streamText = ({
        none = "None",
        loading = "Loading...",
        fine = "Fine",
    })[streamState]
    writeInfo(1, "      Stream: " .. streamText)

    if not playerInfo then
        writeInfo(2, "")
        writeInfo(3, "")
        writeInfo(4, "")
        writeInfo(6, "")
        writeInfo(7, "")
        writeInfo(8, "")
        writeInfo(9, "")
    else
        local info = playerInfo

        writeInfo(2, "       Frame: " .. utils.round(info.frame, 2))
        writeInfo(3, "  Render Dur: " .. utils.round(info.avgRenderDuration * 1000, 2) .. "ms")
        writeInfo(4, "Playback Dur: " .. utils.round(info.avgFrameDuration * 1000, 2) .. "ms")

        local bufferText = ({
            [false] = "Loading...",
            [true] = "Fine",
        })[info.isBuffering]
        writeInfo(6, "      Buffer: " .. bufferText)
        writeInfo(7, "Audio Buffer: " .. tostring(info.audioBuffer))
        writeInfo(8, "Video Buffer: " .. tostring(info.videoBuffer))
        writeInfo(9, "Buffer Size: " .. utils.round(info.bufferSize / 1000 / 1000, 1) .. "Mb")
    end
end

function exports.runUILoop()
    while true do
        render()
        os.sleep(0)
    end
end

return exports
