local render = require("ccv.render")
local audio = require("ccv.audio")

local ccv = {}

ccv.renderVideoFrame = render.renderVideoFrame
ccv.playAudioFrame = audio.playAudioFrame

return ccv
