local utils = {}

function utils.yield()
    local id = "ccv:" .. tostring(math.random(0, 10000000))
    os.queueEvent(id)
    os.pullEvent(id)
end

return utils
