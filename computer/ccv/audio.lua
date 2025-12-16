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
    if #frame == 0 then
        return
    end

    local buffer = table.pack(string.byte(frame, 1, #frame))
    for i = 1, #buffer, 1 do
        buffer[i] = buffer[i] - 128
    end

    playAudioToSpeakers(speakers, buffer)
end

return audio
