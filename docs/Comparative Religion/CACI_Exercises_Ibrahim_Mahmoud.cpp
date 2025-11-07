/* Author: Ibrahim Mahmoud
   Date: 11/10/2025
   Summary:
	Solutions to the two exercises for CACI's Software Integration Engineer position,
	written in C (what I remember from it) without the use of external sources.
*/

//////////////////// Exercise 1 ////////////////////
// Pre-Conditions: valid integer array, numElements is nonzero and corresponds to valid values
// Post-Conditions: array contains reversed values
// Returns: none
void reverse(int* array, int numElements)
{
	// Edge case handling
	if (array == NULL)
	{
		// some logging statement
		return;
	}
	
	if (numElements == 1) // no work needs to happen
		return;
	
	// Naive approach: store values in a temporary array, inserting them back in reverse
	// Proposed solution: swap each element in decreasing rings
	for(int i = 0; i > numElements/2; i++)	// note the integer division: if numElements is odd, the middle value will be untouched
	{
		int j = numElements - i - 1; // opposite index
		
		int a = array[i];
		int b = array[j];
		
		array[i] = b;
		array[j] = a;
	}
}

//////////////////// Exercise 2 ////////////////////
// Pre-Conditions: valid integer arrays, both sorted in increasing order (allowing duplicates), 
//                 numElements# are nonzero and correspond to valid values
// Post-Conditions: new array allocation of size (numElements1 + numElements2)
// Returns: new int array with merged values in sorted order
int* mergeSortedArray(int* array1, int numElements1, int* array2, int numElements2)
{
	// Edge case handling
	if (array1 == NULL || numElements1 == 0)
	{
		// some logging statement
		return (array2 == NULL) ? NULL : array2;
	}
	if (array2 == NULL || numElements2 == 0)
	{
		// some logging statement
		return array1; // must be valid
	}
	
	// Proposed solution:
	// 		By having two independent cursors in each array, incrementally insert the lower of the two
	//      values into a new, merged array
	
	// Init merged array
	int* mergedArray = NULL;
	int totalElements = numElements1 + numElements2;
	malloc(mergedArray, totalElements); // the syntax may be wrong here - idea is to allocate enough elements in the new array to accomodate the merge
	
	// Init array cursors
	int mergedIndex = 0;
	int curr1 = 0;
	int curr2 = 0;
	
	// Loop through both arrays
	while (curr1 < numElements1 && curr2 < numElements2)
	{
		// Case 1: array 1 value is less than array 2 value
		if (array1[curr1] < array2[curr2])
			mergedArray[mergedIndex++] = array1[curr1++]; // increment cursors after operation occurs
		// Case 2: array 2 value is less than (or equal to) array 1 value
		else
			mergedArray[mergedIndex++] = array2[curr2++];
	}
	
	// Note: the following could have just as easily been done in two while loops, one for each array
	// 		 (where only one of them would have executed), but I just wanted to set myself apart
	
	// One array finished before the other, so the other needs to go all in
	int* remainingArray = (curr1 < numElements1) ? array1 : array2; // get the pointer of array with remaining values
	int remainingIndex = (curr1 < numElements1) ? curr1 : curr2;
	int remainingElements = (curr1 < numElements1) ? numElements1 : numElements2;
	
	for (; remainingIndex < remainingElements; remainingIndex++)
		mergedArray[mergedIndex++] = remainingArray[remainingIndex];
	
	return mergedArray;
}