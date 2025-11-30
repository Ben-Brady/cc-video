local utils = require("utils")
local renderer = require("render")
local createReader = require("reader")
local ui = require("ui")
local display = require("display")
local requests = require("requests")
local streams = require("streams")
local player = require("player")

-- display.calibrate()

local function playVideo()
    ui.initialise()
    local stream_id = requests.createYoutubeStream("7AeXrnyv7RA")
    local stream = streams.connectToStream(stream_id)
    utils.safecall(function() player.playStream(stream) end)
    stream.close()
end


while true do
    -- write("Options: ")
    utils.safecall(playVideo)
    sleep(2)
end
