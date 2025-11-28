local utils = require("utils")
local renderer = require("render")
local createReader = require("reader")
local display = require("display")
local requests = require("requests")
local streams = require("streams")

local INITIAL_BUFFER_SIZE = 100
local MAX_BUFFER_SIZE = 200
local BATCH_SIZE = 20
local AUDIO_OFFSET = 0

display.resetMonitors()
-- display.calibrate()


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

local monitor = peripheral.wrap("left")
local width, height = monitor.getSize()

local window_banner = window.create(monitor, 1, 1, width, 1, true)
local window_info = window.create(monitor, 2, 3, width, height - 2, true)

local function writeInfo(y, text)
    window_info.setVisible(false)
    window_info.setCursorPos(1, y)
    window_info.clearLine()
    window_info.write(text)
    window_info.setVisible(true)
end

local HTTP_SERVER = "http://localhost:8000"
local WS_SERVER = "ws://localhost:8000"
local function playVideo()
    local monitors = display.getMonitors()

    writeInfo(5, "      Stream: Starting")
    local stream_id = requests.createYoutubeStream("5BwygBWGhRQ")

    writeInfo(5, "      Stream: Loading")
    local stream = streams.connectToStream(stream_id)
    local buffer = stream.buffer

    print("Connected to Stream")
    local frames = 0


    local speakers = { peripheral.find("speaker") }
    ---@type Speaker
    local speaker = speakers[1]

    local is_over = false

    local function refreshBuffer()
        utils.waitUntilTrue(function()
            return is_over or (#buffer.video > INITIAL_BUFFER_SIZE)
        end)
        utils.waitUntilTrue(function()
            return is_over or (not stream.has_audio or (#buffer.audio > INITIAL_BUFFER_SIZE))
        end)
    end

    local function ensureBuffer()
        local needs_more_data = #buffer.video == 0 or (stream.has_audio and #buffer.audio == 0)

        if not is_over and needs_more_data then
            writeInfo(6, "      Buffer: Loading...")
            refreshBuffer()
        end
    end

    local function playVideoFrame()
        parallel.waitForAll(
            function()
                if not stream.has_audio then
                    return
                end

                local audio_data = table.remove(buffer.audio, 1)
                if audio_data then
                    local audio_buffer = textutils.unserialiseJSON(audio_data)
                    playAudioToSpeakers(audio_buffer)
                end
            end,
            function()
                local video_frame = table.remove(buffer.video, 1)
                if video_frame then
                    renderer.renderVideoFrame(video_frame, monitors)
                end
            end
        )
    end

    local function preloadSpeakers()
        if not stream.has_audio then
            return
        end

        local ADVANCE = 3
        for i = 1, ADVANCE, 1 do
            utils.waitUntilTrue(function()
                return is_over or #buffer.audio > 0
            end)
        end

        local audio_data = table.remove(buffer.audio, 1)
        if audio_data then
            local audio_frame = textutils.unserialiseJSON(audio_data)
            playAudioToSpeakers(audio_frame)
        end
    end

    local function play()
        preloadSpeakers()
        local videoStart = os.clock()
        ensureBuffer()

        while true do
            if is_over and (#buffer.video == 0 and #buffer.audio == 0) then
                return
            end

            local frameTimer = utils.createAverageTimer("frame-start")
            ensureBuffer()

            local renderTimer = utils.createAverageTimer("render-start")
            playVideoFrame()
            local frameDuration = frameTimer.get()
            local renderDuration = renderTimer.get()
            local totalDuration = os.clock() - videoStart

            writeInfo(1, "        Time: " .. utils.round(totalDuration, 2) .. "s")
            writeInfo(2, "  Render Dur: " .. utils.round(renderDuration * 1000, 2) .. "ms")
            writeInfo(3, "Playback Dur: " .. utils.round(frameDuration * 1000, 2) .. "ms")
            if is_over then
                writeInfo(5, "      Stream: Ended")
            else
                writeInfo(5, "      Stream: Fine")
            end
            writeInfo(6, "      Buffer: Fine")
            writeInfo(7, "Audio Buffer: " .. tostring(#buffer.audio))
            writeInfo(8, "Video Buffer: " .. tostring(#buffer.video))

            local size = 0
            for _, frame in ipairs(buffer.audio) do
                size = size + #frame
            end
            for _, frame in ipairs(buffer.video) do
                size = size + #frame
            end

            writeInfo(9, " Buffer Size: " .. utils.round(size / 1024 / 1024, 1) .. "mb")
        end
    end

    parallel.waitForAll(stream.receive, play)
    stream.close()
end


window_banner.setBackgroundColor(colors.gray)
window_banner.setTextColor(colors.lightBlue)

local BANNER = "YOUTUBE PLAYER"
window_banner.write(string.rep(" ", width))

window_banner.setCursorPos((width - #BANNER) / 2, 1)
window_banner.write(BANNER)

local mw, mh = display.getIndivualMonitorSize()
local res_w = tostring(display.MONITOR_ROWS * mw)
local res_h = tostring(display.MONITOR_COLS * mh)
writeInfo(11, "   Resolution: " .. res_w .. "x" .. res_h)
writeInfo(12, "         Rows: " .. tostring(display.MONITOR_ROWS) .. " x " .. tostring(mw) .. "px")
writeInfo(13, "         Cols: " .. tostring(display.MONITOR_COLS) .. " x " .. tostring(mh) .. "px")
while true do
    local success, msg = pcall(playVideo)
    if not success then
        print(msg)
    end
    sleep(2)
end
