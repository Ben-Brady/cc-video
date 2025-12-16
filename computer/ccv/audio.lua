local audio = {}

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
function audio.playAudioFrame(frame, speakers)
    -- local buffer = table.pack(string.byte(frame, 1, #frame))
    -- for i = 1, #buffer, 1 do
    --     buffer[i] = 127 - buffer[i]
    -- end
    local buffer = textutils.unserialiseJSON(frame)
    if #buffer > 0 then
        playAudioToSpeakers(speakers, buffer)
    end
end

return audio
