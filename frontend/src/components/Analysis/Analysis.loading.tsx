import { Divider, Skeleton } from '@mui/material';

const AnalysisSkeleton = () => {

  return (
    <div>

      <div className='flex flex-col gap-1.5'>
        <Skeleton variant="text" height="1rem" />
        <Skeleton variant="text" height="2rem" />

        <Skeleton variant="text" width="50%" />
        <Skeleton variant="text" width="50%" />
        <Skeleton variant="text" width="50%" />

        <Divider />

        <Skeleton variant='rounded' height="16rem" />

      </div>


    </div >
  )
}

export default AnalysisSkeleton;