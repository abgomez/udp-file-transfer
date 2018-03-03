-- adrian protocol example
-- author: Adrian Veliz
-- modified by: Abel Gomez
-- modification log: added custom pattern to identify UDP protocol, updated protocol name

local abel_proto = Proto("Abel","Abel Protocol")

-- create a function to dissect it
function abel_proto.dissector(buffer,pinfo,tree)
    pinfo.cols.protocol = "ABEL"
    local subtree = tree:add(abel_proto,buffer(),"Abel Protocol Data")

	-- Message is at least three bytes long
	if buffer:len() < 3 then
		subtree:add_expert_info(PI_MALFORMED, PI_ERROR, "Invalid Message")
		return end
	
	-- All messages have a sequence number and type
	-- Abel's protocol, new variables to detect specific sections
    local packetType = buffer(0,1):string()
    local packetSequence = buffer(1,1):string()
    local sequenceNo = buffer(2,5):string()
    local message = buffer(7):string()
    
    -- Abel's protocol, new variables to detect specific sections
    subtree:add(buffer(0,1),"Packet Type:     " .. packetType)
    subtree:add(buffer(1,1),"Packet Sequence: " .. packetSequence)
    subtree:add(buffer(2,5),"Sequence Number: " .. sequenceNo)
    subtree:add(buffer(7),  "Message:         " .. message)

	--updated conditions to match custom packet types
    if packetType == "G" then  	-- Request a File
		subtree:add(buffer(2), "GET: " .. buffer(7):string())
	elseif packetType == "P" then -- Send a file
		subtree:add(buffer(2), "PUT: " .. buffer(7):string())
	elseif packetType == "A" then -- acknowledge
		subtree:add(buffer(2), "ACK: " .. buffer(7):string())
	elseif packetType == "D" or packetType == "F" then 	-- Sending Data
		subtree:add(buffer(2),"DATA: " .. buffer(7):string())
		if packetType == "F" then						-- Last Data
			subtree:add_expert_info(PI_RESPONSE_CODE, PI_NOTE, "Finished sending")
		end
	elseif packetType == "E" then -- Error
		subtree:add(buffer(2), "ERROR: " .. buffer(7):string())
		subtree:add_expert_info(PI_RESPONSE_CODE, PI_WARN, "An error during transmission")
	else						-- Unknown message type	
		subtree:add_expert_info(PI_PROTOCOL, PI_WARN, "Unknown message type")
		subtree:add(buffer(0),"ERROR: " .. buffer(0))
	end
end
-- load the udp.port table
udp_table = DissectorTable.get("udp.port")
-- register protocol to handle udp ports
--updated port numbers
udp_table:add(50000,abel_proto)
udp_table:add(50001,abel_proto) 
udp_table:add(50002,abel_proto)
 
-- original source code and getting started
-- https://shloemi.blogspot.com/2011/05/guide-creating-your-own-fast-wireshark.html

-- helpful links
-- https://delog.wordpress.com/2010/09/27/create-a-wireshark-dissector-in-lua/
-- https://wiki.wireshark.org/LuaAPI/Tvb
-- http://lua-users.org/wiki/LuaTypesTutorial
-- https://wiki.wireshark.org/Lua/Examples
-- https://wiki.wireshark.org/LuaAPI/Proto
-- https://www.wireshark.org/docs/wsdg_html_chunked/wslua_dissector_example.html
-- https://www.wireshark.org/lists/wireshark-users/201206/msg00010.html
-- https://wiki.wireshark.org/LuaAPI/TreeItem
-- https://www.wireshark.org/docs/man-pages/tshark.html

