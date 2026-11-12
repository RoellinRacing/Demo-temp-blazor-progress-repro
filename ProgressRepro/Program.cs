using System.Globalization;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using ProgressRepro;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");

// Select the application culture after the initial WASM boot has started.
// RunAsync loads the selected culture's satellite assemblies before rendering.
var culture = CultureInfo.GetCultureInfo("de");
CultureInfo.DefaultThreadCurrentCulture = culture;
CultureInfo.DefaultThreadCurrentUICulture = culture;

await builder.Build().RunAsync();
