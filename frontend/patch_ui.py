import re

filepath = "app/dashboard/observability/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove the KPI cards grid entirely
pattern_cards = r'<div className="grid grid-cols-2 md:grid-cols-4 gap-4">.*?</div>\s*<!-- Charts Section -->'
if '<!-- Charts Section -->' not in content:
    pattern_cards = r'<div className="grid grid-cols-2 md:grid-cols-4 gap-4">.*?</div>\s*\{\/\* Charts Section \*\/\}'

# Using DOTALL for multiline matching
new_content = re.sub(pattern_cards, '{/* Charts Section */}', content, flags=re.DOTALL)

# 2. Add the 3 new charts right before the closing </div> of the charts grid
new_charts = """
                <Card className="border-border rounded-xl shadow-md overflow-hidden bg-card/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      AI Token Usage Timeline
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {!dashboard?.ai_gateway?.chart_data ? (
                      <div className="h-[220px] w-full flex items-center justify-center border border-dashed border-border rounded-lg bg-card/40">
                        <Activity className="h-8 w-8 text-muted-foreground/30 animate-pulse" />
                      </div>
                    ) : (
                      <div className="h-[220px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={dashboard.ai_gateway.chart_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="tokenG" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />
                            <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} dy={10} />
                            <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                            <Tooltip
                              cursor={{ stroke: 'hsl(var(--primary))', strokeWidth: 1, strokeDasharray: '4 4' }}
                              contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                            />
                            <Area type="monotone" dataKey="total_tokens" name="Tokens" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#tokenG)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border rounded-xl shadow-md overflow-hidden bg-card/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Average Workflow Duration (24H)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {!dashboard?.executions?.chart_data ? (
                      <div className="h-[220px] w-full flex items-center justify-center border border-dashed border-border rounded-lg bg-card/40">
                        <Activity className="h-8 w-8 text-muted-foreground/30 animate-pulse" />
                      </div>
                    ) : (
                      <div className="h-[220px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={dashboard.executions.chart_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="wfDurG" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />
                            <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} dy={10} />
                            <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                            <Tooltip
                              cursor={{ stroke: 'hsl(var(--border))', strokeWidth: 1, strokeDasharray: '4 4' }}
                              contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                            />
                            <Area type="monotone" dataKey="avg_duration" name="Avg Duration (s)" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#wfDurG)" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border rounded-xl shadow-md overflow-hidden bg-card/30 lg:col-span-2">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Workflow Success vs Failure Trend
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {!dashboard?.executions?.chart_data ? (
                      <div className="h-[220px] w-full flex items-center justify-center border border-dashed border-border rounded-lg bg-card/40">
                        <Activity className="h-8 w-8 text-muted-foreground/30 animate-pulse" />
                      </div>
                    ) : (
                      <div className="h-[220px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={dashboard.executions.chart_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.5} />
                            <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} dy={10} />
                            <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }} />
                            <Tooltip
                               cursor={{ fill: 'hsl(var(--muted)/0.5)' }}
                               contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                            />
                            <Bar dataKey="success" name="Success" stackId="a" fill="#10b981" />
                            <Bar dataKey="failed" name="Failed" stackId="a" fill="#f43f5e" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </CardContent>
                </Card>
"""

# The closing tag of the charts grid is followed by the Top Active Connectors Bottom List
closing_pattern = r'(\s*)(\<\/div\>\s*\{\/\* Top Active Connectors Bottom List \*\/\})'

new_content = re.sub(closing_pattern, r'\n' + new_charts + r'\1\2', new_content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Modifications applied successfully.")
