--Abel Gomez
--Dissector to debug sliding windows protocol.
--This dissector can identify the different section of UDP datagrams
local sliding_proto = Proto("Sliding","Sliding Windowsl")

-- create a function to dissect it
function sliding_proto.dissector(buffer,pinfo,tree)
    pinfo.cols.protocol = "Sliding"
    local subtree = tree:add(sliding_proto,buffer(),"Sliding Window Protocol Data")

	-- Message is at least three bytes long
	if buffer:len() < 4 then
		subtree:add_expert_info(PI_MALFORMED, PI_ERROR, "Invalid Message")
		return end
	
    -- All messages have a sequence number and type
    -- The first byte is always the type
    -- From the second until the first comma we have the sequence
    -- After the first comma we have the message
    local packetType = buffer(0,1):string()
    local tempString = buffer(0):string() --We need to figure our where the sequence ends
    local seqIndex = string.find(tempString, ',') --get the first occurrence
    local packetSequence = buffer(1,seqIndex-2):string()
    
    -- Display packet's sections
    subtree:add("Packet Type:     " .. packetType)
    subtree:add("Packet Sequence: " .. packetSequence)

    --packet types
    if packetType == "G" then  	-- Request a File
		subtree:add(buffer(2), "GET: " .. buffer(seqIndex):string())
	elseif packetType == "P" then -- Send a file
		subtree:add(buffer(2), "PUT: " .. buffer(seqIndex):string())
	elseif packetType == "A" then -- acknowledge
		subtree:add(buffer(2), "ACK: " .. buffer(seqIndex):string())
	elseif packetType == "D" or packetType == "F" then 	-- Sending Data
		subtree:add(buffer(2),"DATA: " .. buffer(seqIndex):string())
		if packetType == "F" then						-- Last Data
			subtree:add_expert_info(PI_RESPONSE_CODE, PI_NOTE, "Finished sending")
		end
	elseif packetType == "E" then -- Error
		subtree:add(buffer(2), "ERROR: " .. buffer(seqIndex):string())
		subtree:add_expert_info(PI_RESPONSE_CODE, PI_WARN, "An error during transmission")
	else						-- Unknown message type	
		subtree:add_expert_info(PI_PROTOCOL, PI_WARN, "Unknown message type")
		subtree:add(buffer(0),"ERROR: " .. buffer(0))
	end
end
-- load the udp.port table
udp_table = DissectorTable.get("udp.port")
-- register protocol to handle udp ports
udp_table:add(50000,sliding_proto)
udp_table:add(50001,sliding_proto) 
udp_table:add(50002,sliding_proto)
