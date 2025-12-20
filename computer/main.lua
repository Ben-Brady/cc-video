local ccv = require("ccv")
local player = require("ccv-player")
local utils = require("utils")
local displays = require("displays")
local requests = require("requests")
local streams = require("streams")
local ui = require("ui")

local function playVideo()
    ui.initialise()

    local display = displays.getDisplay()
    ---@type Speaker[]
    local speakers = { peripheral.find("speaker") }

    ui.setStream("loading")
    -- local stream_id = requests.createYoutubeStream("9GJSOS9YN7g", display)
    -- local stream_id = requests.createLiveStream(display)
    local stream_id = requests.createFileStream("slop.mp4", display)
    ui.setStream("fine")

    local stream = streams.connectToStream(stream_id, 40, 10)
    utils.safecall(function()
        local play = player.createPlayer(stream, display, speakers)
        ui.updatePlayerDebug(play.debug)
        play.run()
    end)

    ui.updatePlayerDebug(nil)
    ui.setStream("none")
    stream.close()
end


local function renderFrame()
    local display = displays.getDisplay()
    while true do
        pcall(function()
            local frame = requests.downloadTestImage(display)
            ccv.renderVideoFrame(frame, display.monitors)
        end)
        sleep(1)
    end
end


-- Uncomment to calibrate monitors
-- display.calibrate()

renderFrame()
-- while true do
-- parallel.waitForAny(
--     function()
--         utils.safecall(playVideo)
--     end,
--     ui.runUILoop
-- )
-- sleep(2)
-- end
