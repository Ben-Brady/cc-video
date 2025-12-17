local player = require("ccv-player")
local utils = require("utils")
local display = require("display")
local requests = require("requests")
local streams = require("streams")
local log = require("log")
local ui = require("ui")


local function playVideo()
    local monitors = display.getMonitors()
    ---@type Speaker[]
    local speakers = { peripheral.find("speaker") }

    ui.initialise()
    ui.setStream("loading")
    local stream_id = requests.createYoutubeStream("9GJSOS9YN7g")
    -- local stream_id = requests.createLiveStream()
    -- local stream_id = requests.createFileStream("slop.mp4")

    ui.setStream("fine")
    local stream = streams.connectToStream(stream_id, 40, 10)
    utils.safecall(function()
        local play = player.createPlayer(stream, monitors, speakers)
        ui.updatePlayerDebug(play.debug)
        play.run()
    end)
    ui.updatePlayerDebug(nil)
    ui.setStream("none")
    stream.close()
end

display.initialise()
-- Uncomment to calibrate monitors
-- display.calibrate()

while true do
    parallel.waitForAny(
        function()
            utils.safecall(playVideo)
        end,
        ui.runUILoop
    )
    sleep(2)
end
