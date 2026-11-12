# Blazor WebAssembly startup progress regression

Standalone reproduction for [dotnet/aspnetcore#67979](https://github.com/dotnet/aspnetcore/issues/67979). The app starts the WebAssembly runtime in `en-US`, selects German during managed startup, and renders one greeting from each of seven German satellite assemblies. Blazor fetches those assemblies during `WebAssemblyHost.RunAsync()` before rendering the first component.

The page displays Blazor's built-in progress and records changes in `sessionStorage`. The observer reads the framework's CSS custom properties. It does not set them or inject progress values. The satellite assemblies are built from a generic `.resx` and served as ordinary static files.

## Reproduce

Install .NET SDK 10.0.100 and Python 3. From the repository root:

```sh
dotnet publish ProgressRepro/ProgressRepro.csproj -c Release -o publish
python3 scripts/serve.py publish/wwwroot
```

1. Open `http://127.0.0.1:8080/` in Chromium with DevTools open.
2. Look for `PROGRESS DECREASED` in Console and for seven `/_framework/de/*.resources.*.wasm` requests in Network.
3. After the page renders, run `JSON.parse(sessionStorage.getItem('blazor-progress-repro'))` to retrieve the raw samples.
4. Repeat with **Disable cache** checked. When unchecked, reload to test a warm cache.

The browser check can also run through Playwright:

```sh
python3 -m pip install playwright==1.62.0
python3 -m playwright install chromium --only-shell
python3 scripts/measure.py http://127.0.0.1:8080/ traces.json
```

The SDK restores the .NET WebAssembly and Blazor packages from NuGet. This project uses managed trimming and Webcil and does not require the optional `wasm-tools` workload.

## Observed result

Tested with .NET SDK 10.0.100, .NET and Blazor WebAssembly 10.0.0, Debian 13 x64, and Chrome for Testing Headless Shell 150.0.7871.46. The Release build was served over loopback HTTP. In this test runner, MSBuild's WebAssembly and ILLink tasks had to run in-process because local IPC was restricted. No application or framework runtime code was patched.

| Browser HTTP cache | Runs | Observed decrease |
| --- | ---: | --- |
| Enabled, one cold start and two warm reloads | 3 | 100% → 87.5% in each run |
| Disabled via Chrome DevTools Protocol | 2 | 100% → 87.5% in each run |

The first 100% occurs at 41 of 41 resources. The seven satellite requests start afterward. When the first satellite is counted, progress becomes 42 of 48 resources (87.5%). It then reaches 100% again before the app displays all seven greetings. The app selects a startup culture in managed code, and Blazor handles the resulting downloads and updates its own counter. The [raw traces](evidence/traces.json) include the browser's progress samples and timestamps for each satellite request.
