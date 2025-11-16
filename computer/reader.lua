---@param data string
return function(data)
    local offset = 1

    ---@param length number
    ---@return string
    local function readText(length)
        local sub_start = offset
        local sub_end = offset + length - 1
        local sub = string.sub(data, sub_start, sub_end)
        offset = offset + length
        return sub
    end

    ---@param length number
    ---@return number
    local function readHex(length)
        local hex = readText(length)
        local number = tonumber("0x" .. hex)
        if number == nil then
            error(hex .. " is not hex")
        end
        return number
    end

    return { readHex = readHex, read = readText }
end
