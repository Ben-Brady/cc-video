local exports = {}

function exports.yield()
    local id = "ccv:" .. tostring(math.random(0, 10000000))
    os.queueEvent(id)
    os.pullEvent(id)
end

function exports.waitUntilTrue(func)
    local id = "ccv:" .. tostring(math.random(0, 10000000))
    while true do
        local success = func()
        if success then
            return
        end

        os.queueEvent(id)
        os.pullEvent(id)
    end
end


function exports.createAverage(func)
    local total = 0
    local count = 0

    return function(value)
        total = total + value
        count = count + 1
        return total / count
    end
end

return exports
