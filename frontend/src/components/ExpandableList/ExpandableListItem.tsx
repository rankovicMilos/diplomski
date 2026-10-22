import { ExpandLess, ExpandMore } from "@mui/icons-material"
import { IconButton } from "@mui/material"
import { MouseEvent, useState } from "react"
import HighlightedText from "../HighlightedText/HighlightedText"
import cn from "@/src/utils/cn"

export type ListItemType = {
  label: string,
  items: ListItemType[],
}

type ExpandableListItemProps = {
  listItem: ListItemType,
  onItemSelect?: (item: string) => void,
  searchQuery?: string,
  selectedItem?: string,
  // Labels of items that start expanded (e.g. the path to the selected item)
  openItems?: string[],
  className?: string
}

const ExpandableListItem = ({ listItem, onItemSelect, searchQuery, selectedItem, openItems, className }: ExpandableListItemProps) => {

  // While searching, every (already filtered) item starts expanded so matches are visible
  const [open, setOpen] = useState(() => !!searchQuery?.trim() || !!openItems?.includes(listItem.label))

  const handleItemSelect = () => {
    onItemSelect?.(listItem.label)
  }

  const handleOpenItem = (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    setOpen(!open);
  }

  return (
    <div className={cn("flex flex-col pl-3 py-0.5 text-charcoal-80", className)}>
      <div className="flex justify-between items-center">

        <button className={cn("text-start", selectedItem === listItem.label && "font-bold text-teal-100")} onClick={handleItemSelect}>
          <HighlightedText text={listItem.label} highlightText={searchQuery} />
        </button>
        {listItem.items.length ? (
          <IconButton onClick={handleOpenItem} size="small">
            {open ?
              <ExpandLess /> : <ExpandMore />
            }
          </IconButton>
        ) : null}
      </div>

      {open && listItem.items.map(item => <ExpandableListItem key={item.label} listItem={item} onItemSelect={onItemSelect} searchQuery={searchQuery} selectedItem={selectedItem} openItems={openItems} />)}
      {/* {open && <ExpandableList list={listItem.items} onItemSelect={onItemSelect} searchQuery={searchQuery} />} */}
    </div>
  )


}

export default ExpandableListItem;
