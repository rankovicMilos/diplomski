'use client'
import { DeleteOutlined, ImageOutlined, InsertDriveFileOutlined, Percent, PictureAsPdfOutlined } from "@mui/icons-material";
import { Button, Checkbox, IconButton, InputAdornment, MenuItem, Select, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import DragAndDropFile, { UploadedFile } from "../../DragAndDropFile/DragAndDropFile";
import useGenerateMarketPositionMutation from "@/src/hooks/queries/useGenerateMarketPositionMutation";
import useUploadPdfFileMutation from "@/src/hooks/queries/useUploadPdfFileMutation";
import useUploadSheetFileMutation from "@/src/hooks/queries/useUploadSheetFileMutation";
import { useRouter } from "next/navigation";
import { getIndustryById } from "@/src/lib/industries";

const electricityNaceCode = getIndustryById("electricity")?.naceCodes[0] ?? ""

// TODO: duplicated from NewAnalysisForm with Electricity commodities, until they are read from the database.
const ElectricityNewAnalysisForm = () => {

  const { mutateAsync: generateMarketPosition } = useGenerateMarketPositionMutation();
  const { mutateAsync: uploadPdfFile } = useUploadPdfFileMutation();
  const { mutateAsync: uploadSheetFile } = useUploadSheetFileMutation();

  const [isPending, setIsPending] = useState(false);
  const [showAnalysisGenerated, setShowAnalysisGenerated] = useState(false);
  const [error, setError] = useState("")
  const [timeoutError, setTimeoutError] = useState("")

  const [clientDataFile, setClientDataFile] = useState<UploadedFile>();
  const [clientPeerFile, setClientPeerFile] = useState<UploadedFile>();
  const [companyName, setCompanyName] = useState("")
  const [curreny, setCurrency] = useState("RSD")
  const [rateEurDin, setRateEurDin] = useState("117.5")
  const [rateDate, setRateDate] = useState(() => new Date().toISOString().split('T')[0])

  const router = useRouter()


  const currencyOptions = ["RSD"]

  const [crops, setCrops] = useState([
    {
      label: "Hydro",
      name: "hydro",
      isSelected: true,
      revenue_pct: 25
    },
    {
      label: "Coal",
      name: "coal",
      isSelected: true,
      revenue_pct: 25
    },
    {
      label: "Wind",
      name: "wind",
      isSelected: true,
      revenue_pct: 25
    },
    {
      label: "Solar",
      name: "solar",
      isSelected: true,
      revenue_pct: 25
    }
  ])

  const getFileIcon = (type: string) => {
    if (type.startsWith("image/")) return <ImageOutlined />;
    if (type.includes("pdf") || type.includes("document")) return <PictureAsPdfOutlined />;
    return <InsertDriveFileOutlined />;
  };

  const selectedCropsRevenueTotal = useMemo(() => {
    return crops
      .filter(crop => crop.isSelected)
      .reduce((sum, crop) => sum + (crop.revenue_pct || 0), 0)
  }, [crops])

  const isRevenueValid = selectedCropsRevenueTotal > 0 && selectedCropsRevenueTotal <= 100

  // TODO: Coala and Checkpoint files are temporarily optional.
  const isFormValid = useMemo(() => (
    !!companyName && !!curreny && !!rateEurDin && !!rateDate && isRevenueValid
  ), [companyName, curreny, rateDate, rateEurDin, isRevenueValid])

  const generateFileId = () => {
    const uuid = crypto.randomUUID().replace(/-/g, '');
    const timestamp = Date.now().toString(16).padStart(12, '0');
    const combined = timestamp + uuid.slice(12);
    return `${combined.slice(0, 8)}-${combined.slice(8, 12)}-${combined.slice(12, 16)}-${combined.slice(16, 20)}-${combined.slice(20, 32)}`;
  };

  const onSubmit = async () => {
    if (!isFormValid) return

    try {
      setIsPending(true)

      // Upload PDF file first (if provided)
      const uploadPdfRes = clientDataFile ? await uploadPdfFile(clientDataFile) : undefined;

      const fileId = generateFileId()

      // Then generate market position
      const marketPositionBody = {
        analysis_id: fileId,
        analysis_type: "market_position",
        nace_code: electricityNaceCode,
        client_data_key: uploadPdfRes?.data.key,
        client_name: companyName,
        commodities: crops.filter(crop => crop.isSelected).map(crop => ({
          name: crop.name,
          revenue_pct: crop.revenue_pct
        })),
        primary_currency: "RSD",
        fx_rate_eur_rsd: Number(rateEurDin),
        fx_rate_date: rateDate
      }


      generateMarketPosition(marketPositionBody).then(res => {
        console.log(res.data)
        setShowAnalysisGenerated(true)
        const analysisId = res.data?.analysis_id.split('/')[1];
        if (analysisId) {
          router.push(`/analysis/client-position?id=${analysisId}`)
        }
      }).catch(error => {
        const isTimeoutError = error instanceof Error && (
          error.message.includes('timeout') ||
          error.message.includes('Timeout') ||
          error.name === 'TimeoutError' ||
          (error as { code?: string }).code === 'ECONNABORTED'
        );
        if (isTimeoutError) {
          setTimeoutError('Market position generation timed out, continuing with sheet upload...');
        } else {
          setError((error as Error).message);
        }
      }).finally(() => {
        setIsPending(false)
      })



      // Upload sheet file (needs base64 conversion), if provided
      if (clientPeerFile) {
        const base64 = await fileToBase64(clientPeerFile.file);

        await uploadSheetFile({ fileName: `${fileId}.${clientPeerFile.name.split('.').at(-1)}`, base64 });
      }


    } catch (error) {
      console.error('Failed to upload files:', error);
      setError((error as Error).message);
    }
  }

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix (e.g., "data:application/pdf;base64,")
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
    });
  }

  const toggleCropSelected = (cropName: string) => {
    setCrops(prevCrops =>
      prevCrops.map(crop =>
        crop.name === cropName
          ? { ...crop, isSelected: !crop.isSelected }
          : crop
      )
    )
  }

  const updateCropRevenue = (cropName: string, value: string) => {
    const parsed = parseInt(value, 10)
    const validRevenue = isNaN(parsed) ? 0 : Math.max(0, parsed)
    setCrops(prevCrops =>
      prevCrops.map(crop =>
        crop.name === cropName
          ? { ...crop, revenue_pct: validRevenue }
          : crop
      )
    )
  }

  if (showAnalysisGenerated) return (
    <div>
      <h2>Report generated! :)</h2>
    </div>
  )

  if (error) return (
    <div>
      <p className="text-red-100 mb-4">{error}</p>
      <p>Please try again later</p>
    </div>
  )

  if (timeoutError) return (
    <div>
      <h2>This action took longer than expected, please return to the home page or try again</h2>
    </div>
  )

  return (
    <>
      <div className="flex flex-col gap-3">

        <div className="grid grid-cols-6 gap-x-2 gap-y-6">
          <TextField value={companyName} onChange={(e) => setCompanyName(e.target.value)} size="small" label="Company name" className="col-span-5" required />
          <Select value={curreny} onChange={(e) => setCurrency(e.target.value)} size="small" className="col-span-1">
            {currencyOptions.map(currencyOption => <MenuItem key={currencyOption} value={currencyOption}>{currencyOption}</MenuItem>)}
          </Select>
          <TextField value={rateEurDin} onChange={(e) => setRateEurDin(e.target.value)} type="number" size="small" label="Rate EUR-DIN" className="col-span-2" required />
          <TextField value={rateDate} onChange={(e) => setRateDate(e.target.value)} type="date" size="small" label="Rate date" className="col-span-2" required />
        </div>
      </div>
      <div className="flex flex-col gap-3">
        <h5 className="text-md font-semibold">Coala file (.pdf, optional):</h5>
        {clientDataFile ?
          <div key={clientDataFile.id} className="border-1 border-steel-100 bg-steel-20 px-4 py-2 rounded-xs flex justify-between place-items-center">
            <div className="flex gap-1 text-charcoal-60">
              {getFileIcon(clientDataFile.type)}
              <span className="text-charcoal-90 text-sm">
                {clientDataFile?.name}
              </span>
            </div>
            <IconButton onClick={() => setClientDataFile(undefined)}>
              <DeleteOutlined />
            </IconButton>
          </div> :
          <DragAndDropFile onSelectFile={(file) => setClientDataFile(file)} />
        }
      </div>

      <div className="flex flex-col gap-3">
        <h5 className="text-md font-semibold">Commodities: </h5>
        {crops.map((crop) => (
          <div key={crop.name} className="flex gap-3 items-center">
            <Checkbox checked={crop.isSelected} onChange={() => toggleCropSelected(crop.name)} />
            <p className="w-[98px]">{crop.label}</p>
            <TextField
              size="small"
              type="number"
              value={crop.revenue_pct}
              onChange={(e) => updateCropRevenue(crop.name, e.target.value)}
              disabled={!crop.isSelected}

              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <Percent />
                    </InputAdornment>
                  ),
                },
              }}
              required
            />
          </div>
        ))}
        {!isRevenueValid && (
          <p className="text-red-100 text-xs">
            Total revenue percentage must be between values 0 and 100 (current: {selectedCropsRevenueTotal}%)
          </p>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <h5 className="text-md font-semibold">Checkpoint file (.xls, optional):</h5>
        {clientPeerFile ?
          <div key={clientPeerFile.id} className="border-1 border-steel-100 bg-steel-20 px-4 py-2 rounded-xs flex justify-between place-items-center">
            <div className="flex gap-1 text-charcoal-60">
              {getFileIcon(clientPeerFile.type)}
              <span className="text-charcoal-90 text-sm">
                {clientPeerFile?.name}
              </span>
            </div>
            <IconButton onClick={() => setClientPeerFile(undefined)}>
              <DeleteOutlined />
            </IconButton>
          </div> :
          <DragAndDropFile onSelectFile={(file) => setClientPeerFile(file)} />
        }
      </div>

      <Button onClick={onSubmit} loading={isPending} disabled={!isFormValid}>Generate UAF</Button>
    </>
  )
}

export default ElectricityNewAnalysisForm