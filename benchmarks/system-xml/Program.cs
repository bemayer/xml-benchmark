using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Xml;
using System.Xml.Linq;
using System.Xml.XPath;

var op = args[0];
var file = args[1];
var iterations = int.Parse(args[2]);
var xmlBytes = File.ReadAllBytes(file);

switch (op)
{
    case "dom_parse":
    {
        for (int i = 0; i < Math.Min(5, iterations); i++)
            XDocument.Load(new MemoryStream(xmlBytes));
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
            XDocument.Load(new MemoryStream(xmlBytes));
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"dom_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    case "sax_parse":
    {
        for (int i = 0; i < Math.Min(5, iterations); i++)
        {
            using var reader = XmlReader.Create(new MemoryStream(xmlBytes));
            while (reader.Read()) { }
        }
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            using var reader = XmlReader.Create(new MemoryStream(xmlBytes));
            while (reader.Read()) { }
        }
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"sax_parse\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    case "xpath_query":
    {
        var doc = XDocument.Load(new MemoryStream(xmlBytes));
        for (int i = 0; i < Math.Min(5, iterations); i++)
            doc.XPathSelectElements("//*[@id]").GetEnumerator().MoveNext();
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            int count = 0;
            foreach (var _ in doc.XPathSelectElements("//*[@id]")) count++;
        }
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"xpath_query\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    case "serialize":
    {
        var doc = XDocument.Load(new MemoryStream(xmlBytes));
        for (int i = 0; i < Math.Min(5, iterations); i++)
            doc.ToString();
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
            doc.ToString();
        sw.Stop();
        var ms = sw.Elapsed.TotalMilliseconds / iterations;
        Console.WriteLine($"{{\"library\":\"System.Xml\",\"language\":\"C#\",\"operation\":\"serialize\",\"file\":\"{file}\",\"iterations\":{iterations},\"time_ms\":{ms:F3}}}");
        break;
    }
    default:
        Console.WriteLine($"{{\"skipped\":true,\"operation\":\"{op}\",\"library\":\"System.Xml\"}}");
        break;
}
