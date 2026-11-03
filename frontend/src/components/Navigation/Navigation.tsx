'use client'
import { Search } from "@mui/icons-material";
import { InputAdornment, TextField } from "@mui/material";
import ExpandableList from "../ExpandableList/ExpandableList";
import { useQueryState } from "nuqs";
import cn from "@/src/utils/cn";
import { useRouter } from "next/navigation";
import naceCategories, { filterNaceTree, findNacePath, getNaceCode } from "@/src/lib/naceCategories";
import { useMemo } from "react";

const Navigation = () => {


  const router = useRouter()
  const [searchQuery, setSearchQuery] = useQueryState("search", { defaultValue: "" });
  const [category] = useQueryState("category", { defaultValue: "" });

  const filteredCategories = useMemo(() => filterNaceTree(searchQuery, naceCategories), [searchQuery])
  const selectedPath = useMemo(() => findNacePath(category), [category])

  const selectItem = (itemLabel: string) => {
    // Keep the search so the filtered menu stays as it is after selecting
    const params = new URLSearchParams({ category: getNaceCode(itemLabel) })
    if (searchQuery) params.set("search", searchQuery)
    router.push(`/?${params.toString()}`)
  }

  return (
    <div className={cn("sticky top-20 h-[calc(100vh-5rem)] w-[36%] min-w-[340px]",
      "flex flex-col shrink-0  overflow-y-auto self-start scrollbar-thin [scrollbar-gutter:stable]",
      "px-4 border-r-1 border-charcoal-25  pt-8 gap-6 pb-10 bg-steel-10"
    )}>
      <h3 className="text-charcoal-100 font-bold text-lg">NACE hijerarhija</h3>
      <TextField className="bg-white-100" size="small" fullWidth placeholder="Pretraga" slotProps={{
        input: {
          startAdornment: (<InputAdornment position="start">
            <Search />
          </InputAdornment>)
        }
      }} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value || null)} />
      {/* Remount on search change so expanded state is recalculated (all open while searching, selected path otherwise) */}
      <ExpandableList
        key={searchQuery}
        list={filteredCategories}
        onItemSelect={selectItem}
        searchQuery={searchQuery}
        selectedItem={selectedPath.at(-1)}
        openItems={selectedPath.slice(0, -1)}
      />
      {filteredCategories.length === 0 && <p className="text-charcoal-80 text-sm">Nijedna NACE šifra ne odgovara pretrazi „{searchQuery}“</p>}
    </div>
  )
}

export default Navigation;