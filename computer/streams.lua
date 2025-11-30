local exports = {}

local renderer = require("render")
local ui = require("ui")
local createReader = require("reader")
local display = require("display")
local utils = require("utils")
local requests = require("requests")


local INITIAL_BUFFER_SIZE = 100
local MAX_BUFFER_SIZE = 200
local BATCH_SIZE = 20

---@class Stream
local stream_type = {}


---@type {audio: string[], video: string[]}
stream_type.buffer                        = {}
stream_type.has_audio                     = false
stream_type.is_over                       = false

stream_type.receive                       = function() end
stream_type.close                         = function() end
stream_type.ensureBufferSuffienctlyLoaded = function() end
---@return string|nil
stream_type.nextAudioFrame                = function() end
---@return string|nil
stream_type.nextVideoFrame                = function() end
---@param size number
stream_type.waitForAudioBuffer            = function(size) end
---@param size number
stream_type.waitForVideoBuffer            = function(size) end


---@param stream_id string
---@return Stream
function exports.connectToStream(stream_id)
    ui.setStream("loading")
    local ws_video = requests.connectToVideoStream(stream_id)
    local ws_audio = requests.connectToAudioStream(stream_id)

    local video_buffer = {}
    local audio_buffer = {}

    local is_over = false
    local has_audio = ws_audio ~= nil
    local function receive()
        parallel.waitForAll(function()
            if not ws_audio then
                return
            end

            while true do
                utils.waitUntilTrue(function()
                    return #audio_buffer < MAX_BUFFER_SIZE
                end)
                ws_audio.send(tostring(BATCH_SIZE))
                for i = 1, BATCH_SIZE, 1 do
                    local audio_frame = ws_audio.receive()
                    if audio_frame == "END" then
                        return
                    end
                    audio_buffer[#audio_buffer + 1] = audio_frame
                end
            end
        end, function()
            while true do
                utils.waitUntilTrue(function()
                    return #video_buffer < MAX_BUFFER_SIZE
                end)
                ws_video.send(tostring(BATCH_SIZE))
                for i = 1, BATCH_SIZE, 1 do
                    local video_frame = ws_video.receive()
                    if video_frame == "END" then
                        print("Returning")
                        return
                    end
                    video_buffer[#video_buffer + 1] = video_frame
                end
            end
        end)
        is_over = true
        ui.setStream("ended")
    end

    ---@param size number
    local function waitForVideoBuffer(size)
        utils.waitUntilTrue(function()
            return is_over or (#video_buffer > size)
        end)
    end

    ---@param size number
    local function waitForAudioBuffer(size)
        utils.waitUntilTrue(function()
            return is_over or (#audio_buffer > size)
        end)
    end

    ---@return string
    local function nextVideoFrame()
        return table.remove(video_buffer, 1)
    end

    ---@return string|nil
    local function nextAudioFrame()
        local data = table.remove(audio_buffer, 1)
        if not data then
            return nil
        end

        return textutils.unserialiseJSON(data)
    end

    local function ensureBufferSuffienctlyLoaded()
        local needs_more_data = #video_buffer == 0 or (has_audio and #audio_buffer == 0)
        -- print("is_over", is_over)
        -- print("needs_more_data", needs_more_data)

        if not is_over and needs_more_data then
            ui.setBufferLoading(true)
            waitForVideoBuffer(INITIAL_BUFFER_SIZE)
            if has_audio then
                waitForAudioBuffer(INITIAL_BUFFER_SIZE)
            end
            ui.setBufferLoading(false)
        end
    end

    local function close()
        pcall(ws_video.close)
        if ws_audio then
            pcall(ws_audio.close)
        end
    end

    return {
        receive = receive,
        close = close,
        is_over = is_over,
        ensureBufferSuffienctlyLoaded = ensureBufferSuffienctlyLoaded,
        waitForVideoBuffer = waitForVideoBuffer,
        waitForAudioBuffer = waitForAudioBuffer,
        nextVideoFrame = nextVideoFrame,
        nextAudioFrame = nextAudioFrame,
        has_audio = has_audio,
        buffer = {
            video = video_buffer,
            audio = audio_buffer
        },
    }
end

return exports
