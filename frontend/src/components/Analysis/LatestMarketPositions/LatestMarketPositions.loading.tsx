import { Skeleton } from '@mui/material';

const LatestMarketPositionSkeleton = () => {

  return (
    <div className="flex flex-col gap-4 my-3">
      <Skeleton variant="rounded" height="6rem" sx={{ borderRadius: "1.5rem" }} />
      <Skeleton variant="rounded" height="6rem" sx={{ borderRadius: "1.5rem" }} />
      <Skeleton variant="rounded" height="6rem" sx={{ borderRadius: "1.5rem" }} />


    </div>
  )
}

export default LatestMarketPositionSkeleton;