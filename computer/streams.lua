local exports = {}

local renderer = require("render")
local createReader = require("reader")
local display = require("display")
local utils = require("utils")
local requests = require("requests")


local INITIAL_BUFFER_SIZE = 100
local MAX_BUFFER_SIZE = 200
local BATCH_SIZE = 20

---@param stream_id string
function exports.connectToStream(stream_id)
    local ws_video = requests.connectToVideoStream(stream_id)
    local ws_audio = requests.connectToAudioStream(stream_id)

    local video_buffer = {}
    local audio_buffer = {}

    local is_over = false
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
                        return
                    end
                    video_buffer[#video_buffer + 1] = video_frame
                end
            end
        end)
        print("Stream Over")
        is_over = true
    end

    local function close()
        pcall(function()
            if ws_audio then
                ws_audio.close()
            end
        end)
        pcall(function()
            ws_video.close()
        end)
    end

    return {
        receive = receive,
        close = close,
        has_audio = ws_audio ~= nil,
        buffer = {
            video = video_buffer,
            audio = audio_buffer
        },
    }
end

return exports
