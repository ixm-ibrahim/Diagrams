/*
 * Created by SharpDevelop.
 * User: ixmib
 * Date: 10/19/2022
 * Time: 3:35 PM
 * 
 * To change this template use Tools | Options | Coding | Edit Standard Headers.
 */
using System;

namespace Tmp
{
	class Program
	{
		public static void Main(string[] args)
		{
			Console.WriteLine("Enter degrees: ");
			var str = Console.ReadLine();
			
			var degrees = Convert.ToDouble(str);
			var radians = degrees * Math.PI / 180;
			int count = (int)Math.Round(360 / degrees);
			int count90 = (int)Math.Round(90 / degrees);
			const int MAX_DIM = 100;
			
			string strBeforeName = "<shape name=\"";
			string strBeforeNum = " Degrees Arc ";
			string strBeforeX1 = "\" h=\"100\" w=\"100\" aspect=\"variable\" strokewidth=\"inherit\">\n  <connections>\n    <constraint x=\"0\" y=\"0\" perimeter=\"1\" />\n    <constraint x=\"0.5\" y=\"0\" perimeter=\"1\" />\n    <constraint x=\"1\" y=\"0\" perimeter=\"1\" />\n    <constraint x=\"0\" y=\"0.5\" perimeter=\"1\" />\n    <constraint x=\"1\" y=\"0.5\" perimeter=\"1\" />\n    <constraint x=\"0\" y=\"1\" perimeter=\"1\" />\n    <constraint x=\"0.5\" y=\"1\" perimeter=\"1\" />\n    <constraint x=\"1\" y=\"1\" perimeter=\"1\" />\n  </connections>\n  <background>\n    <path>\n      <move x=\"";
			string strBeforeX2 = "\"/>\n      <line x=\"";
			string strBeforeX3 = "\"/>\n      <line x=\"";
			string strBeforeSweep = "\"/>\n      <arc rx=\"100\" ry=\"100\" x-axis-rotation=\"0\" large-arc-flag=\"0\" sweep-flag=\"";
			string strBeforeXr = "\" x=\"";
			string strBeforeY = "\" y=\"";
			string strEnd = "\"/>\n    </path>\n  </background>\n  <foreground>\n    <fillstroke/>\n  </foreground>\n</shape>\n";
			
			// First quarter
			double cx = 0;
			double cy = 0;
			double x1 = MAX_DIM;
			double y1 = 0;
			for (int i = 1; i <= count90; i++)
			{
				double x2 = Math.Round(MAX_DIM * Math.Cos(i*radians), 4);
				double y2 = Math.Round(MAX_DIM * Math.Sin(i*radians), 4);
				
				Console.WriteLine(strBeforeName
								+ degrees
								+ strBeforeNum
								+ i
								+ strBeforeX1
								+ x1
								+ strBeforeY
								+ y1
								+ strBeforeX2
								+ cx
								+ strBeforeY
								+ cy
								+ strBeforeX3
								+ x2
								+ strBeforeY
								+ y2
								+ strBeforeSweep
								+ "0"
								+ strBeforeXr
								+ x1
								+ strBeforeY
								+ y1
								+ strEnd);
				x1 = x2;
				y1 = y2;
			}
			// Second quarter
			cx = MAX_DIM;
			cy = 0;
			x1 = 0;
			y1 = 0;
			for (int i = 1; i <= count90; i++)
			{
				double x2 = Math.Round(MAX_DIM - (MAX_DIM * Math.Cos(i*radians)), 4);
				double y2 = Math.Round(MAX_DIM * Math.Sin(i*radians), 4);
				
				Console.WriteLine(strBeforeName
								+ degrees
								+ strBeforeNum
								+ (i + count90)
								+ strBeforeX1
								+ x1
								+ strBeforeY
								+ y1
								+ strBeforeX2
								+ cx
								+ strBeforeY
								+ cy
								+ strBeforeX3
								+ x2
								+ strBeforeY
								+ y2
								+ strBeforeSweep
								+ "1"
								+ strBeforeXr
								+ x1
								+ strBeforeY
								+ y1
								+ strEnd);
				x1 = x2;
				y1 = y2;
			}
			// Third quarter
			cx = 0;
			cy = MAX_DIM;
			x1 = MAX_DIM;
			y1 = MAX_DIM;
			for (int i = 1; i <= count90; i++)
			{
				double x2 = Math.Round(MAX_DIM * Math.Cos(i*radians), 4);
				double y2 = Math.Round(MAX_DIM - (MAX_DIM * Math.Sin(i*radians)), 4);
				
				Console.WriteLine(strBeforeName
								+ degrees
								+ strBeforeNum
								+ (i + 2*count90)
								+ strBeforeX1
								+ x1
								+ strBeforeY
								+ y1
								+ strBeforeX2
								+ cx
								+ strBeforeY
								+ cy
								+ strBeforeX3
								+ x2
								+ strBeforeY
								+ y2
								+ strBeforeSweep
								+ "1"
								+ strBeforeXr
								+ x1
								+ strBeforeY
								+ y1
								+ strEnd);
				x1 = x2;
				y1 = y2;
			}
			// Fourth quarter
			cx = MAX_DIM;
			cy = MAX_DIM;
			x1 = 0;
			y1 = MAX_DIM;
			for (int i = 1; i <= count90; i++)
			{
				double x2 = Math.Round(MAX_DIM - (MAX_DIM * Math.Cos(i*radians)), 4);
				double y2 = Math.Round(MAX_DIM - (MAX_DIM * Math.Sin(i*radians)), 4);
				
				Console.WriteLine(strBeforeName
								+ degrees
								+ strBeforeNum
								+ (i + 3*count90)
								+ strBeforeX1
								+ x1
								+ strBeforeY
								+ y1
								+ strBeforeX2
								+ cx
								+ strBeforeY
								+ cy
								+ strBeforeX3
								+ x2
								+ strBeforeY
								+ y2
								+ strBeforeSweep
								+ "0"
								+ strBeforeXr
								+ x1
								+ strBeforeY
								+ y1
								+ strEnd);
				x1 = x2;
				y1 = y2;
			}
			
			Console.Write("Press any key to continue . . . ");
			Console.ReadKey(true);
		}
	}
}