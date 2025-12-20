local ccv = {}

local byte = string.byte
local sub = string.sub
local rep = string.rep
local format = string.format
local pack = table.pack
local unpack = table.unpack
local blshift = bit.blshift

local function yield()
    local id = "ccv:" .. tostring(math.random(0, 10000000))
    os.queueEvent(id)
    os.pullEvent(id)
end

---@param speakers Speaker[]
---@param buffer number[]
local function playAudioToSpeakers(speakers, buffer)
    local funcs = {}
    for i, speaker in ipairs(speakers) do
        funcs[#funcs + 1] = function()
            local name = peripheral.getName(speaker)
            while not speaker.playAudio(buffer) do
                local _, target_name = os.pullEvent("speaker_audio_empty")
            end
            os.pullEvent("speaker_audio_empty")
        end
    end
    parallel.waitForAll(table.unpack(funcs))
end

---@param frame string
---@param speakers Speaker[]
function ccv.playAudioFrame(frame, speakers)
    if #frame == 0 then
        return
    end

    local buffer = table.pack(string.byte(frame, 1, #frame))
    for i = 1, #buffer, 1 do
        buffer[i] = buffer[i] - 128
    end

    playAudioToSpeakers(speakers, buffer)
end

---@class VideoFrame
---@field monitors FrameMonitorData[]

---@class FrameMonitorData
---@field index number
---@field palette number[]
---@field rows BlitData[]

---@alias BlitData {text: string, fg: string, bg: string}

---@param data string
---@return VideoFrame
local function parseVideoFrame(data)
    local length = byte(data, 1)

    ---@type FrameMonitorData[]
    local monitors = {}

    local offset = 2
    for mi = 1, length, 1 do
        local index = byte(data, offset)
        local width = byte(data, offset + 1)
        local height = byte(data, offset + 2)
        offset = offset + 3

        local palette = {}
        for pi = 1, 16, 1 do
            local r = byte(data, offset)
            local g = byte(data, offset + 1)
            local b = byte(data, offset + 2)
            offset = offset + 3

            local color = (
                blshift(r, 16)
                + blshift(g, 8)
                + b
            )
            palette[pi] = color
        end

        ---@type BlitData[]
        local rows = {}
        local hex_format = rep("%02X", width)
        for y = 1, height, 1 do
            local text_end = offset + width
            local text = sub(data, offset, text_end - 1)

            local blit = format(hex_format, byte(data, text_end, text_end + width - 1))
            local fg = sub(blit, 1, width)
            local bg = sub(blit, width + 1)

            offset = offset + (width * 2)
            rows[y] = { text, fg, bg }
        end

        monitors[mi] = {
            index = index,
            palette = palette,
            rows = rows
        }

        if mi % 5 == 0 then
            yield()
        end
    end

    return {
        monitors = monitors
    }
end


---@param data string
---@param monitors Monitor[]
function ccv.renderVideoFrame(data, monitors)
    local frame = parseVideoFrame(data)

    for _, section in ipairs(frame.monitors) do
        local monitor = monitors[section.index]
        local setPaletteColor = monitor.setPaletteColor
        local setCursorPos = monitor.setCursorPos
        local blit = monitor.blit

        for i, color in ipairs(section.palette) do
            local paletteIndex = 2 ^ (i - 1)
            setPaletteColor(paletteIndex, color)
        end

        for y, row in ipairs(section.rows) do
            setCursorPos(1, y)
            blit(unpack(row))
        end

        yield()
    end
end

ccv.parseVideoFrame = parseVideoFrame

return ccv
