import ExpandableListItem, { ListItemType } from "./ExpandableListItem";

type ListType = ListItemType[]

type ExpandableListProps = {
  list: ListType,
  onItemSelect?: (item: string) => void,
  searchQuery?: string,
  selectedItem?: string,
  openItems?: string[]
}

const ExpandableList = ({ list, onItemSelect, searchQuery, selectedItem, openItems }: ExpandableListProps) => {

  return (
    <div>
      {list.map(item => <ExpandableListItem key={item.label} listItem={item} onItemSelect={onItemSelect} searchQuery={searchQuery} selectedItem={selectedItem} openItems={openItems} className="text-charcoal-100" />)}
    </div>
  )
}

export default ExpandableList;
