local utils = require("ccv-player.utils")
local ccv = require("ccv")
local parse = require("ccv.parse")

local player = {}

local AUDIO_OFFSET = 4
local INITIAL_BUFFER_SIZE = 100

---@class Player
---@field run fun(): boolean
---@field debug PlayerDebugInfo

---@class PlayerDebugInfo
---@field isBuffering boolean
---@field frame number
---@field avgFrameDuration number
---@field avgRenderDuration number
---@field bufferSize number
---@field videoBuffer number
---@field audioBuffer number


---@param stream Stream
---@param monitors Monitor[]
---@param speakers Speaker[]
---@return Player
function player.createPlayer(stream, monitors, speakers)
    local buffer = stream.buffer
    local frames = 0

    local function playNextAudioFrame()
        if stream.has_audio then
            local frame = stream.nextAudioFrame()
            if frame then
                ccv.playAudioFrame(frame, speakers)
            end
        end
    end

    local function playNextVideoFrame()
        local frame = stream.nextVideoFrame()
        if frame then
            local renderTimer = utils.createAverageTimer("render-start")
            ccv.renderVideoFrame(frame, monitors)
            debug.avgRenderDuration = renderTimer.get()
        end
    end

    local function preloadSpeakers()
        if stream.has_audio then
            stream.wait_for_audio_buffer(AUDIO_OFFSET)

            for i = 1, AUDIO_OFFSET, 1 do
                playNextAudioFrame()
            end
        end
    end

    local function updateDebugBufferInfo()
        debug.audioBuffer = #buffer.audio
        debug.videoBuffer = #buffer.video

        local bufferSize = 0
        for _, value in ipairs(buffer.audio) do
            bufferSize = bufferSize + #value
        end
        for _, value in ipairs(buffer.video) do
            bufferSize = bufferSize + #value
        end
        debug.bufferSize = bufferSize
    end

    ---@type PlayerDebugInfo
    local debug = {
        frame = 0,
        isBuffering = true,
        audioBuffer = 0,
        bufferSize = 0,
        videoBuffer = 0,
        avgFrameDuration = 0,
        avgRenderDuration = 0,
        time = 0,
    }

    local function ensureBufferSuffienctlyLoaded()
        local needs_more_data = #stream.buffer.video == 0 or (stream.has_audio and #stream.buffer.audio == 0)

        if not stream.has_more_data() and needs_more_data then
            debug.isBuffering = true
            stream.wait_for_video_buffer(INITIAL_BUFFER_SIZE)
            if stream.has_audio then
                stream.wait_for_audio_buffer(INITIAL_BUFFER_SIZE)
            end
            debug.isBuffering = false
        end
    end

    local function calculateBufferSize()
        local total = 0
        for _, value in ipairs(stream.buffer.audio) do
            total = total + #value
        end
        for _, value in ipairs(stream.buffer.video) do
            total = total + #value
        end

        return total
    end

    local function play()
        local videoStart = os.clock()
        ensureBufferSuffienctlyLoaded()
        -- utils.yieldUntil(function()
        --     updateDebugBufferInfo()
        --     return stream.is_over
        -- end)
        preloadSpeakers()

        while true do
            local buffersEmpty = #buffer.video == 0 and #buffer.audio == 0
            if not stream.has_more_data() and buffersEmpty then
                return
            end

            local frameTimer = utils.createAverageTimer("frame-start")
            ensureBufferSuffienctlyLoaded()

            parallel.waitForAll(playNextVideoFrame, playNextAudioFrame)
            debug.avgFrameDuration = frameTimer.get()

            debug.frame = debug.frame + 1
            updateDebugBufferInfo()

            debug.videoBuffer = #stream.buffer.video
            debug.audioBuffer = #stream.buffer.audio
            debug.bufferSize = calculateBufferSize()
            utils.yield()
        end
    end

    return {
        debug = debug,
        run = function()
            parallel.waitForAll(stream.receive, play)
        end
    }
end

return player
