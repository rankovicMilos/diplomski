'use client';

import { WarningAmberRounded } from '@mui/icons-material';
import { Avatar, Button } from '@mui/material';


const AnalysisError = () => {

  return (
    <div className="flex justify-center items-center w-full h-full">

      <div className="flex flex-col items-center justify-center gap-6 px-4">
        <div className="flex flex-col items-center gap-3 text-center">
          <Avatar sx={{ width: 56, height: 56, bgcolor: "#d32f2f" }}  > <WarningAmberRounded sx={{ fontSize: 32, color: "#000000" }} /></Avatar>

          <h1 className="text-2xl font-bold text-gray-800">
            Nešto nije u redu
          </h1>

          <p className="text-gray-600 max-w-md">
            Nismo uspeli da učitamo analizu za ovu kategoriju.
          </p>


        </div>

        <Button
          href="/"
          variant="outlined"
          color='inherit'

        >
          Na početnu stranu
        </Button>
      </div>
    </div>
  );
};

export default AnalysisError;