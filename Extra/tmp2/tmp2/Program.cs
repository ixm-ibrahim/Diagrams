/*
 * Created by SharpDevelop.
 * User: ixmib
 * Date: 10/24/2022
 * Time: 1:00 AM
 * 
 * To change this template use Tools | Options | Coding | Edit Standard Headers.
 */
using System;
using System.Drawing;
using System.Drawing.Imaging;

namespace tmp2
{
	class Program
	{
		public static void Main(string[] args)
		{
			Console.WriteLine("Hello World!");
			
			Bitmap bmp = null;
			//using (var image = new Bitmap("C:/Users/ixmib/Downloads/Screenshot 2022-10-24 004758.jpg")) {
			//using (var image = new Bitmap("C:/Users/ixmib/Downloads/Screenshot 2022-10-24 013147.jpg")) {
			//using (var image = new Bitmap("C:/Users/ixmib/Downloads/download.jfif")) {
			//using (var image = new Bitmap("C:/Users/ixmib/Downloads/Screenshot 2022-10-24 015210.jpg")) {
			//using (var image = new Bitmap("C:/Users/ixmib/Downloads/Screenshot 2022-10-24 021425.jpg")) {
			//using (var image = new Bitmap("C:/Users/ixmib/Downloads/download2.png")) {
			using (var image = new Bitmap("C:/Users/ixmib/Downloads/jamarat-ritual-hajj-icon-vector-600w-1627020091.jpg")) {

				bmp = new Bitmap(image);
			}
			int count = 0;
			
			for (int jj = 0; jj < bmp.Height; jj++)
			{
			  for (int ii = 0; ii < bmp.Width; ii++)
			  {
			    Color pixelColor = bmp.GetPixel(ii, jj);
				int b = (int)(GetBrightness(pixelColor));
				//pixelColor = Color.FromArgb(b, pixelColor.R, pixelColor.G, pixelColor.B);
				//pixelColor = Color.FromArgb(255-b, pixelColor.R, pixelColor.G, pixelColor.B);
				
			    //bmp.SetPixel(ii,jj, pixelColor);
			    //if (jj < bmp.Height / 4) Console.WriteLine(pixelColor);
				//if (pixelColor.R > 50)
				//if (jj < 480 || pixelColor.R < 150)
				if (pixelColor.R < 114)
				{
					count++;
					bmp.SetPixel(ii,jj, Color.FromArgb(255, 0, 0, 0));
				}
				else
					bmp.SetPixel(ii,jj, Color.FromArgb(255, 255, 255, 255));
			  }
			}
			
			bmp.Save("C:/Users/ixmib/Downloads/converted3.jpg");
			
			// TODO: Implement Functionality Here
			
			Console.Write("Press any key to continue . . .  " + count);
			Console.ReadKey(true);
		}
	
		public static double GetBrightness(Color color)
		{
		    return (0.2126*color.R + 0.7152*color.G + 0.0722*color.B);
		}
	}
}