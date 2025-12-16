local createReader = require("ccv.reader")
local utils = require("ccv.utils")
local log = require("log")

local parse = {}

---@class VideoFrame
---@field monitors FrameMonitorData[]

---@class FrameMonitorData
---@field index number
---@field palette number[]
---@field rows BlitData[]

---@alias BlitData {text: string, fg: string, bg: string}

---@param data string
---@return VideoFrame
function parse.parseVideoFrame(data)
    local reader = createReader(data)
    local length = reader.readByte()

    ---@type FrameMonitorData[]
    local monitors = {}

    for _ = 1, length, 1 do
        local index = reader.readByte()
        local width = reader.readByte()
        local height = reader.readByte()
        local monitor = monitors[index]

        local palette = {}
        for i = 1, 16, 1 do
            local r = reader.readByte()
            local g = reader.readByte()
            local b = reader.readByte()
            local color = (
                bit.blshift(r, 16)
                + bit.blshift(g, 8)
                + b
            )
            palette[#palette + 1] = color
        end

        ---@type BlitData[]
        local rows = {}
        for y = 1, height, 1 do
            local text = reader.read(width)
            local color = reader.read(width)

            local blit = string.format(string.rep("%02X", width), string.byte(color, 1, #color))
            local fg = string.sub(blit, 1, width)
            local bg = string.sub(blit, width + 1)
            rows[#rows + 1] = { text, fg, bg }
        end

        monitors[#monitors + 1] = {
            index = index,
            palette = palette,
            rows = rows
        }
    end

    return {
        monitors = monitors
    }
end

return parse
