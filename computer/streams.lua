local exports = {}

local ui = require("ui")
local display = require("display")
local utils = require("utils")
local requests = require("requests")


local BATCH_SIZE = 20

---@class Stream
---@field buffer {audio: string[], video: string[]}
---@field has_audio boolean
---@field receive fun(): nil
---@field has_more_data fun(): boolean
---@field close fun(): nil
---@field nextFrame fun(): (video: string, audio: string | nil)|nil
---@field wait_for_audio_buffer fun(size: number): nil
---@field wait_for_video_buffer fun(size: number): nil

---@param streamId string
---@param bufferSize? number
---@param batchSize? number
---@return Stream
function exports.connectToStream(streamId, bufferSize, batchSize)
    bufferSize = bufferSize or 50
    batchSize = bufferSize or 50
    local ws_video = requests.connectToVideoStream(streamId)
    local ws_audio = requests.connectToAudioStream(streamId)

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
                utils.yieldUntil(function()
                    return #audio_buffer < bufferSize
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
                utils.yieldUntil(function()
                    return #video_buffer < bufferSize
                end)
                ws_video.send(tostring(BATCH_SIZE))
                for i = 1, BATCH_SIZE, 1 do
                    local video_frame = ws_video.receive()
                    if video_frame == "END" then
                        return
                    end
                    video_buffer[#video_buffer + 1] = video_frame
                end
            end
        end)
        is_over = true
    end

    ---@param size number
    local function wait_for_video_buffer(size)
        utils.yieldUntil(function()
            return is_over or (#video_buffer > size)
        end)
    end

    ---@param size number
    local function wait_for_audio_buffer(size)
        utils.yieldUntil(function()
            return is_over or (#audio_buffer > size)
        end)
    end

    ---@return boolean
    local function has_more_data()
        return not is_over
    end

    ---@return string
    local function nextVideoFrame()
        local data = table.remove(video_buffer, 1)
        if not data then
            return nil
        end

        return data
    end

    ---@return string|nil
    local function nextAudioFrame()
        ---@type string
        local data = table.remove(audio_buffer, 1)
        if not data then
            return nil
        end
        return data
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
        has_more_data = has_more_data,
        wait_for_video_buffer = wait_for_video_buffer,
        wait_for_audio_buffer = wait_for_audio_buffer,
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
