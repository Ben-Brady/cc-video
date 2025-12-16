local createReader = require("ccv.reader")
local utils = require("ccv.utils")
local log = require("log")
local exports = {}

local colorIndexs = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 }

---@param data string
---@param monitors Monitor[]
function exports.renderVideoFrame(data, monitors)
    local reader = createReader(data)

    local length = reader.readByte()

    for _ = 1, length, 1 do
        local index = reader.readByte()
        local width = reader.readByte()
        local height = reader.readByte()
        local monitor = monitors[index]

        for _, paletteColor in ipairs(colorIndexs) do
            local color = reader.read(3)
            local r, g, b = color:byte(1, 3)
            monitor.setPaletteColor(paletteColor, 255 - r, 255 - g, 255 - b)
        end

        for y = 1, height, 1 do
            local text = reader.read(width)
            local color = reader.read(width)

            local blit = string.format(string.rep("%02X", width), string.byte(color, 1, #color))
            local bgBlit = string.sub(blit, 1, width)
            local fgBlit = string.sub(blit, width + 1)

            monitor.setCursorPos(1, y)
            monitor.blit(text, fgBlit, bgBlit)
        end

        utils.yield()
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
