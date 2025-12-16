local utils = {}

function utils.yieldUntil(func)
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

function utils.createTimer()
    local start = os.clock()

    return {
        get = function()
            return os.clock() - start
        end
    }
end

---@type table<string, function>
local timers = {}

function utils.createAverageTimer(id)
    if timers[id] == nil then
        timers[id] = utils.createAverage()
    end

    local start = os.clock()

    return {
        get = function()
            local duration = os.clock() - start
            local average = timers[id]
            return average(duration)
        end
    }
end

function utils.createAverage()
    local total = 0
    local count = 0

    return function(value)
        total = total + value
        count = count + 1
        return total / count
    end
end

---@param value number
---@param places number
---@return string
function utils.round(value, places)
    return string.format("%.2f", value)
end

---@param func function
---@return boolean
function utils.safecall(func)
    local success, msg = pcall(func)
    if not success then
        print(msg)
    end
    return success
end

function utils.waitForNextTick()
    os.sleep(0)
end

return utils
