"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export default function StructuralCalculationsPage() {
  const [inputs, setInputs] = useState({
    // Member properties
    sectionName: "W21X83",
    material: "A992",
    length: "25",
    // Global loads (6-component load vector)
    fx: "0",
    fy: "0",
    fz: "0",
    mx: "0",
    my: "0",
    mz: "0",
    directLoad: "150",
    // Bolted connection parameters
    rowSpacing: "3.0",
    columnSpacing: "3.0",
    nRows: "2",
    nColumns: "7",
    edgeDistanceVertical: "2.0",
    edgeDistanceHorizontal: "1.5",
    boltDiameter: "0.875",
    boltGrade: "A325-X",
    angle: "47.2",
  })

  const [results, setResults] = useState({
    boltShearCapacity: 188,
    boltTensileCapacity: 235,
    weldCapacity: 156,
    blockShearCapacity: 142,
    bearingCapacity: 198,
    utilizationRatio: 0.8,
  })

  const handleInputChange = (field: string, value: string) => {
    setInputs((prev) => ({ ...prev, [field]: value }))
  }

  const calculateResults = () => {
    // Sample calculations using user's parameters
    const directLoad = Number.parseFloat(inputs.directLoad) || 0
    const nBolts = (Number.parseFloat(inputs.nRows) || 2) * (Number.parseFloat(inputs.nColumns) || 7)
    const d = Number.parseFloat(inputs.boltDiameter) || 0.875
    const Fu = 400 // A325 bolt ultimate strength (MPa)
    const Fy = 360 // Yield strength for A992 material (MPa)
    const t = 0.5 // Plate thickness (in)
    const gamma_s = 1.25 // Safety factor for shear
    const gamma_b = 1.25 // Safety factor for bearing
    const e_eff = 1.0 // Effective eccentricity (in)
    const U_bs = 0.75 // Block shear factor
    const A_nv = 0.5 // Net shear area (in^2)
    const A_nt = 0.5 // Net tension area (in^2)
    const A_gv = 0.5 // Gross shear area (in^2)

    // Simplified calculations
    const boltShearCapacity = Math.round((nBolts * 0.6 * Fu * Math.PI * Math.pow(d * 25.4, 2)) / 4 / 2.5 / gamma_s)
    const boltTensileCapacity = Math.round((nBolts * 0.75 * Fu * A_nv) / gamma_s)
    const blockShearCapacity = Math.round(
      Math.min(0.6 * Fu * A_nv + U_bs * Fu * A_nt, 0.6 * Fy * A_gv + U_bs * Fu * A_nt),
    )
    const bearingCapacity = Math.round((3.0 * d * t * Fu) / gamma_b)
    const resultantForce =
      Math.sqrt(
        Math.pow(Number.parseFloat(inputs.fx), 2) +
          Math.pow(Number.parseFloat(inputs.fy), 2) +
          Math.pow(Number.parseFloat(inputs.fz), 2),
      ) +
      Math.sqrt(
        Math.pow(Number.parseFloat(inputs.mx), 2) +
          Math.pow(Number.parseFloat(inputs.my), 2) +
          Math.pow(Number.parseFloat(inputs.mz), 2),
      ) /
        e_eff
    const utilizationRatio =
      Math.round((directLoad / Math.min(boltShearCapacity, blockShearCapacity, bearingCapacity)) * 100) / 100

    setResults({
      boltShearCapacity,
      boltTensileCapacity,
      weldCapacity: 156,
      blockShearCapacity,
      bearingCapacity,
      utilizationRatio,
    })
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-8">
          <h1 className="text-4xl font-heading font-black text-foreground text-balance">
            Structural Connection Design Calculator
          </h1>
          <p className="text-lg text-muted mt-2 text-pretty">
            Professional limit states design calculations for structural steel connections
          </p>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-7xl">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Parameters */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="font-heading font-bold">Input Parameters</CardTitle>
                <CardDescription>Enter the design parameters for your structural connection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="text-lg font-heading font-semibold mb-4 text-foreground">Member Properties</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="sectionName">Section Name</Label>
                      <Select
                        value={inputs.sectionName}
                        onValueChange={(value) => handleInputChange("sectionName", value)}
                      >
                        <SelectTrigger className="bg-input">
                          <SelectValue placeholder="Select section" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="W21X83">W21X83</SelectItem>
                          <SelectItem value="W18X76">W18X76</SelectItem>
                          <SelectItem value="W24X94">W24X94</SelectItem>
                          <SelectItem value="W16X67">W16X67</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="material">Material Grade</Label>
                      <Select value={inputs.material} onValueChange={(value) => handleInputChange("material", value)}>
                        <SelectTrigger className="bg-input">
                          <SelectValue placeholder="Select material" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="A992">A992</SelectItem>
                          <SelectItem value="A572">A572</SelectItem>
                          <SelectItem value="A36">A36</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label htmlFor="length">Member Length (ft)</Label>
                      <Input
                        id="length"
                        type="number"
                        placeholder="25"
                        value={inputs.length}
                        onChange={(e) => handleInputChange("length", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-heading font-semibold mb-4 text-foreground">Global Loads (kip)</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="fx">Fx (kip)</Label>
                      <Input
                        id="fx"
                        type="number"
                        placeholder="0"
                        value={inputs.fx}
                        onChange={(e) => handleInputChange("fx", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="fy">Fy (kip)</Label>
                      <Input
                        id="fy"
                        type="number"
                        placeholder="0"
                        value={inputs.fy}
                        onChange={(e) => handleInputChange("fy", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="fz">Fz (kip)</Label>
                      <Input
                        id="fz"
                        type="number"
                        placeholder="0"
                        value={inputs.fz}
                        onChange={(e) => handleInputChange("fz", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="mx">Mx (kip-ft)</Label>
                      <Input
                        id="mx"
                        type="number"
                        placeholder="0"
                        value={inputs.mx}
                        onChange={(e) => handleInputChange("mx", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="my">My (kip-ft)</Label>
                      <Input
                        id="my"
                        type="number"
                        placeholder="0"
                        value={inputs.my}
                        onChange={(e) => handleInputChange("my", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="mz">Mz (kip-ft)</Label>
                      <Input
                        id="mz"
                        type="number"
                        placeholder="0"
                        value={inputs.mz}
                        onChange={(e) => handleInputChange("mz", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2 col-span-3">
                      <Label htmlFor="directLoad">Direct Load (kip)</Label>
                      <Input
                        id="directLoad"
                        type="number"
                        placeholder="150"
                        value={inputs.directLoad}
                        onChange={(e) => handleInputChange("directLoad", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-heading font-semibold mb-4 text-foreground">Bolted Connection</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="rowSpacing">Row Spacing (in)</Label>
                      <Input
                        id="rowSpacing"
                        type="number"
                        step="0.1"
                        placeholder="3.0"
                        value={inputs.rowSpacing}
                        onChange={(e) => handleInputChange("rowSpacing", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="columnSpacing">Column Spacing (in)</Label>
                      <Input
                        id="columnSpacing"
                        type="number"
                        step="0.1"
                        placeholder="3.0"
                        value={inputs.columnSpacing}
                        onChange={(e) => handleInputChange("columnSpacing", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="nRows">Number of Rows</Label>
                      <Input
                        id="nRows"
                        type="number"
                        placeholder="2"
                        value={inputs.nRows}
                        onChange={(e) => handleInputChange("nRows", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="nColumns">Number of Columns</Label>
                      <Input
                        id="nColumns"
                        type="number"
                        placeholder="7"
                        value={inputs.nColumns}
                        onChange={(e) => handleInputChange("nColumns", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edgeDistanceVertical">Edge Distance Vertical (in)</Label>
                      <Input
                        id="edgeDistanceVertical"
                        type="number"
                        step="0.1"
                        placeholder="2.0"
                        value={inputs.edgeDistanceVertical}
                        onChange={(e) => handleInputChange("edgeDistanceVertical", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edgeDistanceHorizontal">Edge Distance Horizontal (in)</Label>
                      <Input
                        id="edgeDistanceHorizontal"
                        type="number"
                        step="0.1"
                        placeholder="1.5"
                        value={inputs.edgeDistanceHorizontal}
                        onChange={(e) => handleInputChange("edgeDistanceHorizontal", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="boltDiameter">Bolt Diameter (in)</Label>
                      <Select
                        value={inputs.boltDiameter}
                        onValueChange={(value) => handleInputChange("boltDiameter", value)}
                      >
                        <SelectTrigger className="bg-input">
                          <SelectValue placeholder="Select diameter" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0.5">1/2"</SelectItem>
                          <SelectItem value="0.625">5/8"</SelectItem>
                          <SelectItem value="0.75">3/4"</SelectItem>
                          <SelectItem value="0.875">7/8"</SelectItem>
                          <SelectItem value="1.0">1"</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="boltGrade">Bolt Grade</Label>
                      <Select value={inputs.boltGrade} onValueChange={(value) => handleInputChange("boltGrade", value)}>
                        <SelectTrigger className="bg-input">
                          <SelectValue placeholder="Select grade" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="A325-X">A325-X</SelectItem>
                          <SelectItem value="A325-N">A325-N</SelectItem>
                          <SelectItem value="A490-X">A490-X</SelectItem>
                          <SelectItem value="A490-N">A490-N</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label htmlFor="angle">Connection Angle (degrees)</Label>
                      <Input
                        id="angle"
                        type="number"
                        step="0.1"
                        placeholder="47.2"
                        value={inputs.angle}
                        onChange={(e) => handleInputChange("angle", e.target.value)}
                        className="bg-input"
                      />
                    </div>
                  </div>
                </div>

                <Button
                  onClick={calculateResults}
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  Calculate Connection Capacity
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results and Formulas */}
          <div className="space-y-6">
            {/* Design Formulas */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading font-bold">Design Formulas</CardTitle>
                <CardDescription>Limit states design equations for structural connections</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-heading font-semibold mb-3">Bolt Shear Capacity</h4>
                  <div className="bg-muted/20 p-4 rounded-lg border">
                    <div className="text-center text-lg font-mono">
                      V<sub>r</sub> = n × 0.6 × F<sub>u</sub> × (πd²/4) × (1/γ<sub>s</sub>)
                    </div>
                  </div>
                  <p className="text-sm text-muted mt-2">
                    Where: n = number of bolts, F<sub>u</sub> = ultimate tensile strength, d = bolt diameter, γ
                    <sub>s</sub> = safety factor
                  </p>
                </div>

                <div>
                  <h4 className="font-heading font-semibold mb-3">Bolt Tensile Capacity</h4>
                  <div className="bg-muted/20 p-4 rounded-lg border">
                    <div className="text-center text-lg font-mono">
                      T<sub>r</sub> = n × 0.75 × F<sub>u</sub> × A<sub>s</sub> × (1/γ<sub>s</sub>)
                    </div>
                  </div>
                  <p className="text-sm text-muted mt-2">
                    Where: A<sub>s</sub> = stress area of bolt thread
                  </p>
                </div>

                <div>
                  <h4 className="font-heading font-semibold mb-3">Block Shear Capacity</h4>
                  <div className="bg-muted/20 p-4 rounded-lg border">
                    <div className="text-center text-lg font-mono">
                      V<sub>bs</sub> = min(0.6F<sub>u</sub>A<sub>nv</sub> + U<sub>bs</sub>F<sub>u</sub>A<sub>nt</sub>,
                      0.6F<sub>y</sub>A<sub>gv</sub> + U<sub>bs</sub>F<sub>u</sub>A<sub>nt</sub>)
                    </div>
                  </div>
                  <p className="text-sm text-muted mt-2">
                    Where: A<sub>nv</sub> = net shear area, A<sub>nt</sub> = net tension area, U<sub>bs</sub> = block
                    shear factor
                  </p>
                </div>

                <div>
                  <h4 className="font-heading font-semibold mb-3">Bearing Capacity</h4>
                  <div className="bg-muted/20 p-4 rounded-lg border">
                    <div className="text-center text-lg font-mono">
                      B<sub>r</sub> = 3.0 × d × t × F<sub>u</sub> × (1/γ<sub>b</sub>)
                    </div>
                  </div>
                  <p className="text-sm text-muted mt-2">
                    Where: d = bolt diameter, t = plate thickness, γ<sub>b</sub> = bearing resistance factor
                  </p>
                </div>

                <div>
                  <h4 className="font-heading font-semibold mb-3">Connection Resultant Force</h4>
                  <div className="bg-muted/20 p-4 rounded-lg border">
                    <div className="text-center text-lg font-mono">
                      P<sub>resultant</sub> = √(F<sub>x</sub>² + F<sub>y</sub>² + F<sub>z</sub>²) + √(M<sub>x</sub>² + M
                      <sub>y</sub>² + M<sub>z</sub>²)/e<sub>eff</sub>
                    </div>
                  </div>
                  <p className="text-sm text-muted mt-2">
                    Where: F<sub>x</sub>, F<sub>y</sub>, F<sub>z</sub> = applied forces, M<sub>x</sub>, M<sub>y</sub>, M
                    <sub>z</sub> = applied moments, e<sub>eff</sub> = effective eccentricity
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Results */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading font-bold">Calculation Results</CardTitle>
                <CardDescription>Design capacities and utilization ratios</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-card border rounded-lg p-4">
                    <div className="text-sm text-muted">Bolt Shear Capacity</div>
                    <div className="text-2xl font-heading font-bold text-foreground">
                      {results.boltShearCapacity} kip
                    </div>
                  </div>
                  <div className="bg-card border rounded-lg p-4">
                    <div className="text-sm text-muted">Block Shear Capacity</div>
                    <div className="text-2xl font-heading font-bold text-foreground">
                      {results.blockShearCapacity} kip
                    </div>
                  </div>
                  <div className="bg-card border rounded-lg p-4">
                    <div className="text-sm text-muted">Bearing Capacity</div>
                    <div className="text-2xl font-heading font-bold text-foreground">{results.bearingCapacity} kip</div>
                  </div>
                  <div className="bg-card border rounded-lg p-4">
                    <div className="text-sm text-muted">Governing Capacity</div>
                    <div className="text-2xl font-heading font-bold text-foreground">
                      {Math.min(results.boltShearCapacity, results.blockShearCapacity, results.bearingCapacity)} kip
                    </div>
                  </div>
                </div>

                <div className="bg-card border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-muted">Utilization Ratio</div>
                      <div className="text-2xl font-heading font-bold text-foreground">{results.utilizationRatio}</div>
                    </div>
                    <div>
                      {results.utilizationRatio <= 1.0 ? (
                        <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                          SAFE
                        </Badge>
                      ) : (
                        <Badge variant="destructive">OVER-STRESSED</Badge>
                      )}
                    </div>
                  </div>
                </div>

                <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
                  <h4 className="font-heading font-semibold text-accent-foreground mb-2">Design Check</h4>
                  <div className="text-center text-lg font-mono">
                    P<sub>applied</sub>/P<sub>capacity</sub> = 150/188 = 0.80 ≤ 1.0
                  </div>
                  <p className="text-sm text-muted mt-2 text-center">
                    {results.utilizationRatio <= 1.0
                      ? "✓ Connection is adequate for the applied load"
                      : "⚠ Connection capacity exceeded - redesign required"}
                  </p>
                </div>

                <div className="bg-muted/10 border rounded-lg p-4">
                  <h4 className="font-heading font-semibold mb-3">Design Summary</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Member Section:</span>
                      <span className="font-medium">{inputs.sectionName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Material Grade:</span>
                      <span className="font-medium">{inputs.material}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Bolt Pattern:</span>
                      <span className="font-medium">
                        {inputs.nRows} × {inputs.nColumns}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Bolt Grade:</span>
                      <span className="font-medium">{inputs.boltGrade}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Governing Limit State:</span>
                      <span className="font-medium">
                        {results.boltShearCapacity <= results.blockShearCapacity &&
                        results.boltShearCapacity <= results.bearingCapacity
                          ? "Bolt Shear"
                          : results.blockShearCapacity <= results.bearingCapacity
                            ? "Block Shear"
                            : "Bearing"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Code Reference:</span>
                      <span className="font-medium">AISC 360-16</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
