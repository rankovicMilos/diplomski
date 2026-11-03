'use client'
import { Percent } from "@mui/icons-material";
import { Button, Checkbox, InputAdornment, MenuItem, Select, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import useGenerateMarketPositionMutation from "@/src/hooks/queries/useGenerateMarketPositionMutation";
import { useRouter } from "next/navigation";
import { getIndustryById } from "@/src/lib/industries";

const electricityNaceCode = getIndustryById("electricity")?.naceCodes[0] ?? ""

// TODO: duplicated from NewAnalysisForm with Electricity commodities, until they are read from the database.
const ElectricityNewAnalysisForm = () => {

  const { mutateAsync: generateMarketPosition } = useGenerateMarketPositionMutation();

  const [isPending, setIsPending] = useState(false);
  const [showAnalysisGenerated, setShowAnalysisGenerated] = useState(false);
  const [error, setError] = useState("")
  const [timeoutError, setTimeoutError] = useState("")

  const [companyName, setCompanyName] = useState("")
  const [curreny, setCurrency] = useState("RSD")
  const [totalRevenue, setTotalRevenue] = useState("")
  const [rateEurDin, setRateEurDin] = useState("117.5")
  const [rateDate, setRateDate] = useState(() => new Date().toISOString().split('T')[0])

  const router = useRouter()


  const currencyOptions = ["RSD"]

  const [crops, setCrops] = useState([
    {
      label: "Hidroelektrane",
      name: "hydro",
      isSelected: true,
      revenue_pct: 25
    },
    {
      label: "Ugalj",
      name: "coal",
      isSelected: true,
      revenue_pct: 25
    },
    {
      label: "Vetar",
      name: "wind",
      isSelected: true,
      revenue_pct: 25
    },
    {
      label: "Sunce",
      name: "solar",
      isSelected: true,
      revenue_pct: 25
    }
  ])

  const selectedCropsRevenueTotal = useMemo(() => {
    return crops
      .filter(crop => crop.isSelected)
      .reduce((sum, crop) => sum + (crop.revenue_pct || 0), 0)
  }, [crops])

  const isRevenueValid = selectedCropsRevenueTotal > 0 && selectedCropsRevenueTotal <= 100

  const isFormValid = useMemo(() => (
    !!companyName && !!curreny && !!rateEurDin && !!rateDate && Number(totalRevenue) > 0 && isRevenueValid
  ), [companyName, curreny, rateDate, rateEurDin, totalRevenue, isRevenueValid])

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

      const marketPositionBody = {
        analysis_id: generateFileId(),
        analysis_type: "market_position",
        nace_code: electricityNaceCode,
        client_name: companyName,
        total_revenue: Number(totalRevenue),
        commodities: crops.filter(crop => crop.isSelected).map(crop => ({
          name: crop.name,
          revenue_pct: crop.revenue_pct
        })),
        primary_currency: curreny,
        fx_rate_eur_rsd: Number(rateEurDin),
        fx_rate_date: rateDate
      }

      generateMarketPosition(marketPositionBody).then(res => {
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
          setTimeoutError('Isteklo je vreme za generisanje tržišne pozicije');
        } else {
          setError((error as Error).message);
        }
      }).finally(() => {
        setIsPending(false)
      })
    } catch (error) {
      console.error('Failed to generate analysis:', error);
      setError((error as Error).message);
      setIsPending(false)
    }
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
      <h2>Izveštaj je generisan! :)</h2>
    </div>
  )

  if (error) return (
    <div>
      <p className="text-red-100 mb-4">{error}</p>
      <p>Pokušajte ponovo kasnije</p>
    </div>
  )

  if (timeoutError) return (
    <div>
      <h2>Radnja je trajala duže od očekivanog. Vratite se na početnu stranu ili pokušajte ponovo</h2>
    </div>
  )

  return (
    <>
      <div className="flex flex-col gap-3">

        <div className="grid grid-cols-6 gap-x-2 gap-y-6">
          <TextField value={companyName} onChange={(e) => setCompanyName(e.target.value)} size="small" label="Naziv preduzeća" className="col-span-5" required />
          <Select value={curreny} onChange={(e) => setCurrency(e.target.value)} size="small" className="col-span-1">
            {currencyOptions.map(currencyOption => <MenuItem key={currencyOption} value={currencyOption}>{currencyOption}</MenuItem>)}
          </Select>
          <TextField value={totalRevenue} onChange={(e) => setTotalRevenue(e.target.value)} type="number" size="small" label={`Ukupan prihod (${curreny})`} className="col-span-6" slotProps={{ htmlInput: { min: 0 } }} required />
          <TextField value={rateEurDin} onChange={(e) => setRateEurDin(e.target.value)} type="number" size="small" label="Kurs EUR/RSD" className="col-span-2" required />
          <TextField value={rateDate} onChange={(e) => setRateDate(e.target.value)} type="date" size="small" label="Datum kursa" className="col-span-2" required />
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <h5 className="text-md font-semibold">Proizvodi: </h5>
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
            Zbir procenata učešća u prihodima mora biti veći od 0 i najviše 100 (trenutno: {selectedCropsRevenueTotal}%)
          </p>
        )}
      </div>

      <Button onClick={onSubmit} loading={isPending} disabled={!isFormValid}>Generiši UAF</Button>
    </>
  )
}

export default ElectricityNewAnalysisForm
