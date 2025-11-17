local renderer = require("render")
local createReader = require("reader")
local display = require("display")
local utils = require("utils")

local INITIAL_BUFFER_SIZE = 25
local MAX_BUFFER_SIZE = 30
local BATCH_SIZE = 5
local AUDIO_OFFSET = 0

display.resetMonitors()
-- display.calibrate()

local function playVideo()
    local monitors = display.setupMonitors()

    local r = http.get("http://127.0.0.1:8000/start/video")
    local id = r.readAll()
    local ws_audio = http.websocket("ws://127.0.0.1:8000/audio?id=" .. id)
    local ws_video = http.websocket("ws://127.0.0.1:8000/video?id=" .. id)

    if not ws_video then
        error("Could not connect")
    end
    print("Connected to Stream")
    local frames = 0


    local speakers = { peripheral.find("speaker") }
    ---@type Speaker
    local speaker = speakers[1]

    local averageRender = utils.createAverage()
    local averageFrame = utils.createAverage()

    local video_frames = {}
    local audio_frames = {}

    local is_over = false
    local function streamVideo()
        parallel.waitForAll(function()
            if not ws_audio then
                return
            end

            while true do
                utils.waitUntilTrue(function()
                    return #audio_frames < MAX_BUFFER_SIZE
                end)
                ws_audio.send(tostring(BATCH_SIZE))
                for i = 1, BATCH_SIZE, 1 do
                    local audio_frame = ws_audio.receive()
                    if audio_frame == "END" then
                        return
                    end
                    audio_frames[#audio_frames + 1] = audio_frame
                end
            end
        end, function()
            while true do
                utils.waitUntilTrue(function()
                    return #video_frames < MAX_BUFFER_SIZE
                end)
                ws_video.send(tostring(BATCH_SIZE))
                for i = 1, BATCH_SIZE, 1 do
                    local video_frame = ws_video.receive()
                    if video_frame == "END" then
                        return
                    end
                    video_frames[#video_frames + 1] = video_frame
                end
            end
        end)
        print("Stream Over")
        is_over = true
    end

    local function refreshBuffer()
        utils.waitUntilTrue(function()
            return is_over or (#video_frames > INITIAL_BUFFER_SIZE)
        end)
        utils.waitUntilTrue(function()
            return is_over or (not ws_audio or (#audio_frames > INITIAL_BUFFER_SIZE))
        end)
    end

    local function playVideoFrame(isFirstFrame)
        local needs_more_data = #video_frames == 0 or (ws_audio and #audio_frames == 0)
        if not is_over and needs_more_data then
            print("Refreshing Buffer")
            refreshBuffer()
        end

        if ws_audio and isFirstFrame then
            local buffered = 0
            for i = 1, AUDIO_OFFSET, 1 do
                utils.waitUntilTrue(function() return #audio_frames > 0 end)
                local audio_data = table.remove(audio_frames, 1)
                local buffer = textutils.unserialiseJSON(audio_data)
                speaker.playAudio(buffer, 0.3)
            end
        end

        local start = os.clock()
        parallel.waitForAll(
            function()
                if not ws_audio then
                    return
                end

                local audio_data = table.remove(audio_frames, 1)
                if audio_data then
                    local buffer = textutils.unserialiseJSON(audio_data)

                    while not speaker.playAudio(buffer, 1) do
                        utils.yield()
                    end
                end
            end,
            function()
                local video_frame = table.remove(video_frames, 1)
                if video_frame then
                    renderer.renderVideoFrame(video_frame, monitors)
                end
            end
        )
        local duration = averageRender(os.clock() - start)
        print("Render: " .. math.floor(duration * 10000) / 10 .. "ms")
    end

    local function play()
        playVideoFrame(true)
        while true do
            if is_over and (#video_frames == 0 and #audio_frames == 0) then
                return
            end

            local start = os.clock()
            playVideoFrame(false)
            local duration = averageFrame(os.clock() - start)

            print("Audio Frames: " .. tostring(#audio_frames))
            print("Video Frames: " .. tostring(#video_frames))
            print("Frame: " .. math.floor(duration * 10000) / 10 .. "ms")
        end
    end

    parallel.waitForAll(streamVideo, play)
    pcall(function() ws_video.close() end)
    pcall(function() ws_audio.close() end)
    print("Stream Over")
end



term.redirect(peripheral.wrap("left"))
term.clear()
term.setCursorPos(1, 1)
print("Youtube Player")

while true do
    local success, msg = pcall(playVideo)
    if not success then
        print(msg)
    end
    sleep(2)
end
