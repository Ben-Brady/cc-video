local createReader = require("reader")
local utils = require("utils")
local exports = {}

---@class VideoHeader
---@field fps number
---@field monitorXCount number
---@field monitorYCount number
---@field monitorWidth number
---@field monitorHeight number

---@param f ReadHandle
---@return string
local function getVideoHeader(f)
    local line = f.readLine()
    local header = textutils.unserialiseJSON(data)
end

local colorIndexs = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 }

---@param data string
---@param monitors Monitor[]
function exports.renderVideoFrame(data, monitors)
    local reader = createReader(data)


    for i, monitor in ipairs(monitors) do
        for i, paletteColor in ipairs(colorIndexs) do
            local color = reader.readHex(6)
            monitor.setPaletteColor(paletteColor, color)
        end

        local width, height = monitor.getSize()
        local text = string.rep(string.char(135), width)

        for y = 1, height, 1 do
            monitor.setCursorPos(1, y)
            local bgBlit = reader.read(width)
            local textBlit = reader.read(width)
            monitor.blit(text, bgBlit, textBlit)
        end
        if reader.read(1) ~= "\n" then
            error("Monitor Frame not right size")
        end
    end
end

---@param monitors Monitor[]
function exports.playStream(getNextFrame, monitors)
    local frame = 0
    local start = os.clock()
    while true do
        local data = getNextFrame()
        if data == nil then
            return
        else
            exports.renderVideoFrame(data, monitors)
        end
    end
end

return exports
