-- probe_hello.lua: proves --script Lua runs and L.log reaches log.txt (Step 0 check).
L.on_frame(function(n)
  if n % 600 == 0 then L.log("probe frame " .. n) end
end)
