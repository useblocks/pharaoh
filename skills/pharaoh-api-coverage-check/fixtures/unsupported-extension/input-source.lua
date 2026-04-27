-- Lua module — not in the shared public-symbol-patterns.md table.
local M = {}

function M.load_catalog(path)
  return path
end

function M.save_catalog(path)
  return true
end

return M
