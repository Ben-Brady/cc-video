local ccv = {}

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

        for i, color in ipairs(section.palette) do
            local paletteIndex = 2 ^ (i - 1)
            monitor.setPaletteColor(paletteIndex, color)
        end

        for y, row in ipairs(section.rows) do
            local text, fg, bg = table.unpack(row)
            monitor.setCursorPos(1, y + 1)
            monitor.blit(text, fg, bg)
        end

        yield()
    end
end

return ccv
