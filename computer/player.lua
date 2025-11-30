local utils = require("utils")
local renderer = require("render")
local createReader = require("reader")
local ui = require("ui")
local display = require("display")
local requests = require("requests")
local streams = require("streams")

local exports = {}

local AUDIO_OFFSET = 3

---@type Speaker[]
local speakers = { peripheral.find("speaker") }
local function playAudioToSpeakers(buffer)
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

---@param stream Stream
function exports.playStream(stream)
    ui.setStream("fine")
    local buffer = stream.buffer

    local monitors = display.getMonitors()

    local frames = 0

    local function playAudioFrame()
        if not stream.has_audio then
            return
        end

        local audio_frame = stream.nextAudioFrame()
        if audio_frame then
            playAudioToSpeakers(audio_frame)
        end
    end
    local function playVideoFrame()
        local video_frame = stream.nextVideoFrame()
        if video_frame then
            renderer.renderVideoFrame(video_frame, monitors)
        end
    end

    local function preloadSpeakers()
        if not stream.has_audio then
            return
        end

        stream.waitForAudioBuffer(AUDIO_OFFSET)

        for i = 1, AUDIO_OFFSET, 1 do
            local audio_frame = stream.nextAudioFrame()
            if audio_frame then
                playAudioToSpeakers(audio_frame)
            end
        end
    end

    local function play()
        preloadSpeakers()
        local videoStart = os.clock()
        stream.ensureBufferSuffienctlyLoaded()

        while true do
            if stream.is_over and (#buffer.video == 0 and #buffer.audio == 0) then
                return
            end

            local frameTimer = utils.createAverageTimer("frame-start")
            stream.ensureBufferSuffienctlyLoaded()

            local renderTimer = utils.createAverageTimer("render-start")
            parallel.waitForAll(playVideoFrame, playAudioFrame)

            ui.setFrameInfo({
                time = os.clock() - videoStart,
                frameDuration = frameTimer.get(),
                renderDuration = renderTimer.get(),
                audioBuffer = #buffer.audio,
                videoBuffer = #buffer.video,
            })
        end
    end

    parallel.waitForAll(stream.receive, play)
end

return exports
