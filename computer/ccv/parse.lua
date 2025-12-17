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
    local offset = 1

    local length = string.byte(data, offset)
    offset = offset + 1

    ---@type FrameMonitorData[]
    local monitors = {}

    for j = 1, length, 1 do
        local index = string.byte(data, offset)
        local width = string.byte(data, offset + 1)
        local height = string.byte(data, offset + 2)
        local monitor = monitors[index]
        offset = offset + 3

        local palette = {}
        for i = 1, 16, 1 do
            local r = string.byte(data, offset)
            local g = string.byte(data, offset + 1)
            local b = string.byte(data, offset + 2)
            offset = offset + 3
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
            local text_end = offset + width
            local text = string.sub(data, offset, text_end - 1)

            local color_bytes = table.pack(string.byte(data, text_end, text_end + width - 1))
            local blit = string.format(string.rep("%02X", #color_bytes), table.unpack(color_bytes))
            local fg = string.sub(blit, 1, width)
            local bg = string.sub(blit, width + 1)

            offset = offset + (width * 2)
            rows[#rows + 1] = { text, fg, bg }
        end

        monitors[#monitors + 1] = {
            index = index,
            palette = palette,
            rows = rows
        }

        if j % 5 == 0 then
            utils.yield()
        end
    end

    return {
        monitors = monitors
    }
end

return parse
