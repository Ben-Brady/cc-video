---@param data string
return function(data)
    local offset = 1

    ---@param length number
    ---@return string
    local function read(length)
        local sub_start = offset
        local sub_end = offset + length - 1
        local sub = string.sub(data, sub_start, sub_end)
        offset = offset + length
        return sub
    end

    ---@return number
    local function readByte()
        local char = read(1)
        return string.byte(char)
    end

    return { readByte = readByte, read = read }
end
