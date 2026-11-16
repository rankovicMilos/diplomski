'use client'
import { Close, FilterList, Search } from "@mui/icons-material";
import { Drawer, IconButton, InputAdornment, TextField } from "@mui/material";
import ExpandableList from "../ExpandableList/ExpandableList";
import { useQueryState } from "nuqs";
import { useRouter } from "next/navigation";
import naceCategories, { filterNaceTree, findNacePath, getNaceCode } from "@/src/lib/naceCategories";
import { useMemo, useState } from "react";

// NACE industry filter: a header button that opens a slide-in panel,
// so the page content keeps the full width.
const Navigation = () => {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useQueryState("search", { defaultValue: "" });
  const [category] = useQueryState("category", { defaultValue: "" });

  const filteredCategories = useMemo(() => filterNaceTree(searchQuery, naceCategories), [searchQuery])
  const selectedPath = useMemo(() => findNacePath(category), [category])
  const selectedLabel = selectedPath.at(-1)

  const selectItem = (itemLabel: string) => {
    // Keep the search so the filtered menu stays as it is after selecting
    const params = new URLSearchParams({ category: getNaceCode(itemLabel) })
    if (searchQuery) params.set("search", searchQuery)
    router.push(`/?${params.toString()}`)
    setOpen(false)
  }

  const showAll = () => {
    router.push("/")
    setOpen(false)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        className="inline-flex min-h-11 max-w-[60vw] items-center gap-2 rounded-full border border-white-100/30 bg-white-100/10 px-4 text-xs font-semibold text-white-100 transition-colors duration-200 hover:bg-white-100/20 cursor-pointer"
      >
        <FilterList fontSize="small" aria-hidden />
        <span className="truncate">{selectedLabel ? selectedLabel : "Filter po delatnosti"}</span>
      </button>

      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{ paper: { sx: { width: "min(440px, 100vw)", backgroundColor: "#fff", backgroundImage: "none" } } }}
      >
        <div className="flex h-full flex-col gap-5 px-5 py-6">
          <div className="flex items-center justify-between">
            <h3 className="text-charcoal-100 font-semibold text-md">NACE hijerarhija</h3>
            <IconButton aria-label="Zatvori" onClick={() => setOpen(false)}><Close /></IconButton>
          </div>
          <TextField size="small" fullWidth placeholder="Pretraga" slotProps={{
            input: {
              startAdornment: (<InputAdornment position="start"><Search /></InputAdornment>)
            }
          }} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value || null)} />
          {selectedLabel && (
            <button type="button" onClick={showAll} className="self-start text-xs font-semibold text-teal-100 hover:underline cursor-pointer">
              Prikaži sve delatnosti
            </button>
          )}
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {/* Remount on search change so expanded state is recalculated (all open while searching, selected path otherwise) */}
            <ExpandableList
              key={searchQuery}
              list={filteredCategories}
              onItemSelect={selectItem}
              searchQuery={searchQuery}
              selectedItem={selectedLabel}
              openItems={selectedPath.slice(0, -1)}
            />
            {filteredCategories.length === 0 && <p className="text-charcoal-80 text-sm">Nijedna NACE šifra ne odgovara pretrazi „{searchQuery}“</p>}
          </div>
        </div>
      </Drawer>
    </>
  )
}

export default Navigation;
