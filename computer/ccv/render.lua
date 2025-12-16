local createReader = require("ccv.reader")
local parse = require("ccv.parse")
local utils = require("ccv.utils")
local log = require("log")
local exports = {}

local colorIndexs = { 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 }

---@param data string
---@param monitors Monitor[]
function exports.renderVideoFrame(data, monitors)
    local frame = parse.parseVideoFrame(data)


    for _, section in ipairs(frame.monitors) do
        local monitor = monitors[section.index]

        for i, color in ipairs(section.palette) do
            local colorId = colorIndexs[i]
            monitor.setPaletteColor(colorId, color)
        end

        for y, row in ipairs(section.rows) do
            monitor.setCursorPos(1, y + 1)
            monitor.blit(row.text, row.fg, row.bg)
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
